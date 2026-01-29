package com.riverpermits.app.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val userEmail: String = "",
    val pushEnabled: Boolean = true,
    val emailEnabled: Boolean = true,
    val isLoggedOut: Boolean = false,
    val isAdmin: Boolean = false
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadUserData()
    }

    private fun loadUserData() {
        viewModelScope.launch {
            authRepository.userEmail.collect { email ->
                _uiState.value = _uiState.value.copy(userEmail = email ?: "")
            }
        }
        viewModelScope.launch {
            authRepository.isAdmin.collect { isAdmin ->
                _uiState.value = _uiState.value.copy(isAdmin = isAdmin)
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = _uiState.value.copy(isLoggedOut = true)
        }
    }
}
