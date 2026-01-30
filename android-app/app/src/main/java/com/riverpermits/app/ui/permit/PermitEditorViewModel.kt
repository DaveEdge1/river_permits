package com.riverpermits.app.ui.permit

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.remote.dto.RiverDto
import com.riverpermits.app.data.repository.PermitRepository
import com.riverpermits.app.util.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class PermitEditorUiState(
    val isEditMode: Boolean = false,
    val permitId: Int? = null,
    val name: String = "",
    val selectedRiver: RiverDto? = null,
    val startDate: String = "",
    val endDate: String = "",
    val partySize: Int = 1,
    val enabled: Boolean = true,
    val rivers: List<RiverDto> = emptyList(),
    val isLoading: Boolean = false,
    val isSaving: Boolean = false,
    val error: String? = null,
    val saveSuccess: Boolean = false
)

@HiltViewModel
class PermitEditorViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val permitRepository: PermitRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(PermitEditorUiState())
    val uiState: StateFlow<PermitEditorUiState> = _uiState.asStateFlow()

    init {
        val permitId = savedStateHandle.get<Int>("permitId")
        if (permitId != null && permitId != -1) {
            _uiState.value = _uiState.value.copy(
                isEditMode = true,
                permitId = permitId
            )
            loadPermit(permitId)
        }
        loadRivers()
    }

    private fun loadRivers() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)

            when (val result = permitRepository.getRivers()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        rivers = result.data,
                        isLoading = false
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        error = "Failed to load rivers",
                        isLoading = false
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    private fun loadPermit(permitId: Int) {
        viewModelScope.launch {
            val permit = permitRepository.getPermitById(permitId)
            permit?.let {
                _uiState.value = _uiState.value.copy(
                    name = it.name,
                    startDate = it.startDate,
                    endDate = it.endDate,
                    partySize = it.partySize,
                    enabled = it.enabled
                )
                // Set selected river when rivers are loaded
                _uiState.value.rivers.find { river -> river.facilityId == permit.facilityId }?.let { river ->
                    _uiState.value = _uiState.value.copy(selectedRiver = river)
                }
            }
        }
    }

    fun updateName(name: String) {
        _uiState.value = _uiState.value.copy(name = name, error = null)
    }

    fun selectRiver(river: RiverDto) {
        _uiState.value = _uiState.value.copy(
            selectedRiver = river,
            name = if (_uiState.value.name.isBlank()) river.name else _uiState.value.name,
            error = null
        )
    }

    fun updateStartDate(date: String) {
        _uiState.value = _uiState.value.copy(startDate = date, error = null)
    }

    fun updateEndDate(date: String) {
        _uiState.value = _uiState.value.copy(endDate = date, error = null)
    }

    fun updatePartySize(size: Int) {
        _uiState.value = _uiState.value.copy(partySize = size.coerceIn(1, 50))
    }

    fun updateEnabled(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(enabled = enabled)
    }

    fun save() {
        val state = _uiState.value

        // Validation
        if (state.name.isBlank()) {
            _uiState.value = state.copy(error = "Name is required")
            return
        }
        if (state.selectedRiver == null) {
            _uiState.value = state.copy(error = "Please select a river")
            return
        }
        if (state.startDate.isBlank() || state.endDate.isBlank()) {
            _uiState.value = state.copy(error = "Start and end dates are required")
            return
        }

        viewModelScope.launch {
            _uiState.value = state.copy(isSaving = true, error = null)

            val result = if (state.isEditMode && state.permitId != null) {
                permitRepository.updatePermit(
                    permitId = state.permitId,
                    name = state.name,
                    facilityId = state.selectedRiver.facilityId,
                    startDate = state.startDate,
                    endDate = state.endDate,
                    partySize = state.partySize,
                    enabled = state.enabled
                )
            } else {
                permitRepository.createPermit(
                    name = state.name,
                    facilityId = state.selectedRiver.facilityId,
                    startDate = state.startDate,
                    endDate = state.endDate,
                    partySize = state.partySize
                ).map { Unit }
            }

            when (result) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        saveSuccess = true
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isSaving = false,
                        error = "Failed to save permit"
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
