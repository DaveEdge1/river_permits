package com.riverpermits.app.ui.availability

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.remote.api.ApiService
import com.riverpermits.app.data.remote.dto.AvailabilityRiverDto
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AvailabilityUiState(
    val isLoading: Boolean = false,
    val rivers: List<AvailabilityRiverDto> = emptyList(),
    val totalCount: Int = 0,
    val riverCount: Int = 0,
    val error: String? = null
)

@HiltViewModel
class PermitAvailabilityViewModel @Inject constructor(
    private val apiService: ApiService
) : ViewModel() {

    private val _uiState = MutableStateFlow(AvailabilityUiState())
    val uiState: StateFlow<AvailabilityUiState> = _uiState.asStateFlow()

    fun loadAvailability() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                val response = apiService.getAvailability()

                if (response.isSuccessful) {
                    val body = response.body()
                    if (body != null) {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            rivers = body.rivers,
                            totalCount = body.totalCount,
                            riverCount = body.riverCount
                        )
                        Log.d("AvailabilityVM", "Loaded ${body.totalCount} permits across ${body.riverCount} rivers")
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            error = "Empty response from server"
                        )
                    }
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Failed to load availability: ${response.code()}"
                    )
                }
            } catch (e: Exception) {
                Log.e("AvailabilityVM", "Error loading availability", e)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "Network error: ${e.message}"
                )
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
