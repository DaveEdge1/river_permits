package com.riverpermits.app.ui.auth

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.firebase.messaging.FirebaseMessaging
import com.riverpermits.app.data.model.ApiResult
import com.riverpermits.app.data.repository.AuthRepository
import com.riverpermits.app.data.repository.DeviceRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import javax.inject.Inject

data class LoginUiState(
    val email: String = "",
    val password: String = "",
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val isLoggedIn: Boolean = false
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val deviceRepository: DeviceRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    init {
        checkLoginStatus()
    }

    private fun checkLoginStatus() {
        viewModelScope.launch {
            authRepository.isLoggedIn.collect { isLoggedIn ->
                _uiState.value = _uiState.value.copy(isLoggedIn = isLoggedIn)
            }
        }
    }

    fun onEmailChange(email: String) {
        _uiState.value = _uiState.value.copy(email = email, errorMessage = null)
    }

    fun onPasswordChange(password: String) {
        _uiState.value = _uiState.value.copy(password = password, errorMessage = null)
    }

    fun login() {
        val currentState = _uiState.value

        if (currentState.email.isBlank()) {
            _uiState.value = currentState.copy(errorMessage = "Email is required")
            return
        }

        if (currentState.password.isBlank()) {
            _uiState.value = currentState.copy(errorMessage = "Password is required")
            return
        }

        viewModelScope.launch {
            _uiState.value = currentState.copy(isLoading = true, errorMessage = null)

            val result = authRepository.login(currentState.email, currentState.password)

            when (result) {
                is ApiResult.Success -> {
                    // Register FCM token after successful login
                    registerFcmToken()

                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isLoggedIn = true,
                        errorMessage = null
                    )
                }
                is ApiResult.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )
                }
                ApiResult.Loading -> {
                    // Already handled above
                }
            }
        }
    }

    private suspend fun registerFcmToken() {
        try {
            val token = FirebaseMessaging.getInstance().token.await()
            Log.d(TAG, "FCM token obtained: ${token.take(20)}...")

            val result = deviceRepository.registerDevice(token)
            when (result) {
                is ApiResult.Success -> {
                    Log.d(TAG, "FCM token registered successfully")
                }
                is ApiResult.Error -> {
                    Log.e(TAG, "Failed to register FCM token: ${result.message}")
                }
                ApiResult.Loading -> {}
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to get FCM token", e)
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(errorMessage = null)
    }

    companion object {
        private const val TAG = "LoginViewModel"
    }
}
