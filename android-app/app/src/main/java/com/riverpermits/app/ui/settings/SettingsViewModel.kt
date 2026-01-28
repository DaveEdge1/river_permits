package com.riverpermits.app.ui.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.local.TokenManager
import com.riverpermits.app.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val userEmail: String = "",
    val pushEnabled: Boolean = true,
    val emailEnabled: Boolean = true,
    val isLoggedOut: Boolean = false
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val tokenManager: TokenManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            tokenManager.userEmail.collect { email ->
                _uiState.value = _uiState.value.copy(userEmail = email ?: "")
            }
        }
    }

    fun updatePushEnabled(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(pushEnabled = enabled)
        // TODO: Save to server via API
    }

    fun updateEmailEnabled(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(emailEnabled = enabled)
        // TODO: Save to server via API
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = _uiState.value.copy(isLoggedOut = true)
        }
    }
}
