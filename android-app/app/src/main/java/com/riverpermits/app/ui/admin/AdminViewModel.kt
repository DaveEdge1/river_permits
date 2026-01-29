package com.riverpermits.app.ui.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.model.ApiResult
import com.riverpermits.app.data.repository.AdminRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AdminUiState(
    val isLoading: Boolean = false,
    val testNotifyResult: TestNotifyResult? = null,
    val errorMessage: String? = null
)

data class TestNotifyResult(
    val success: Boolean,
    val message: String,
    val permitsChecked: Int,
    val availablePermits: Int,
    val notificationSent: Boolean,
    val notificationsCleared: Int?
)

@HiltViewModel
class AdminViewModel @Inject constructor(
    private val adminRepository: AdminRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AdminUiState())
    val uiState: StateFlow<AdminUiState> = _uiState.asStateFlow()

    fun testNotify() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = true,
                errorMessage = null,
                testNotifyResult = null
            )

            when (val result = adminRepository.testNotify()) {
                is ApiResult.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        testNotifyResult = TestNotifyResult(
                            success = result.data.success,
                            message = result.data.message,
                            permitsChecked = result.data.permitsChecked,
                            availablePermits = result.data.availablePermits,
                            notificationSent = result.data.notificationSent,
                            notificationsCleared = result.data.notificationsCleared
                        )
                    )
                }
                is ApiResult.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )
                }
                ApiResult.Loading -> {
                    // Already handled
                }
            }
        }
    }

    fun clearResult() {
        _uiState.value = _uiState.value.copy(
            testNotifyResult = null,
            errorMessage = null
        )
    }
}
