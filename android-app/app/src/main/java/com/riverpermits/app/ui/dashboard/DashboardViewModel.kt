package com.riverpermits.app.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.local.entities.PermitEntity
import com.riverpermits.app.data.repository.PermitRepository
import com.riverpermits.app.util.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val permits: List<PermitEntity> = emptyList(),
    val isLoading: Boolean = false,
    val isRefreshing: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val permitRepository: PermitRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        // Observe local permits
        viewModelScope.launch {
            permitRepository.permits.collect { permits ->
                _uiState.value = _uiState.value.copy(permits = permits)
            }
        }

        // Initial load
        refreshPermits()
    }

    fun refreshPermits() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true, error = null)

            when (val result = permitRepository.refreshPermits()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(isRefreshing = false)
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isRefreshing = false,
                        error = "Failed to load permits"
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    fun togglePermit(permitId: Int) {
        viewModelScope.launch {
            when (val result = permitRepository.togglePermit(permitId)) {
                is Result.Success -> {
                    // UI will update automatically via Flow
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        error = "Failed to toggle permit"
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    fun deletePermit(permitId: Int) {
        viewModelScope.launch {
            when (val result = permitRepository.deletePermit(permitId)) {
                is Result.Success -> {
                    // UI will update automatically via Flow
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        error = "Failed to delete permit"
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
