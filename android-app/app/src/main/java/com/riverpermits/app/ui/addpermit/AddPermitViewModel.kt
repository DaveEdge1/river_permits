package com.riverpermits.app.ui.addpermit

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.riverpermits.app.data.remote.dto.RiverDto
import com.riverpermits.app.data.repository.PermitRepository
import com.riverpermits.app.util.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import javax.inject.Inject

data class AddPermitUiState(
    val rivers: List<RiverDto> = emptyList(),
    val selectedRiver: RiverDto? = null,
    val permitName: String = "",
    val startDate: LocalDate = LocalDate.now(),
    val endDate: LocalDate = LocalDate.now().plusMonths(3),
    val partySize: Int = 1,
    val enabled: Boolean = true,
    val isLoading: Boolean = false,
    val isLoadingRivers: Boolean = false,
    val isLoadingPermit: Boolean = false,
    val error: String? = null,
    val isSuccess: Boolean = false,
    val isEditMode: Boolean = false,
    val editPermitId: Int? = null
)

@HiltViewModel
class AddPermitViewModel @Inject constructor(
    private val permitRepository: PermitRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val _uiState = MutableStateFlow(AddPermitUiState())
    val uiState: StateFlow<AddPermitUiState> = _uiState.asStateFlow()

    private val dateFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")

    // Get permit ID from navigation arguments (null or 0 for create, positive for edit)
    private val permitId: Int = savedStateHandle.get<Int>("permitId") ?: 0

    init {
        loadRivers()
        if (permitId > 0) {
            loadPermitForEditing(permitId)
        }
    }

    private fun loadRivers() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingRivers = true)

            when (val result = permitRepository.getRivers()) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        rivers = result.data,
                        isLoadingRivers = false
                    )
                    // If editing, select the correct river after rivers are loaded
                    val state = _uiState.value
                    if (state.isEditMode && state.selectedRiver == null && state.editPermitId != null) {
                        val editPermit = permitRepository.getPermitById(state.editPermitId)
                        if (editPermit != null) {
                            val matchingRiver = result.data.find { it.facilityId == editPermit.facilityId }
                            if (matchingRiver != null) {
                                _uiState.value = _uiState.value.copy(selectedRiver = matchingRiver)
                            }
                        }
                    }
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoadingRivers = false,
                        error = "Failed to load rivers"
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    private fun loadPermitForEditing(permitId: Int) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoadingPermit = true, isEditMode = true, editPermitId = permitId)

            val permit = permitRepository.getPermitById(permitId)
            if (permit != null) {
                // Find matching river
                val matchingRiver = _uiState.value.rivers.find { it.facilityId == permit.facilityId }

                _uiState.value = _uiState.value.copy(
                    isLoadingPermit = false,
                    permitName = permit.name,
                    startDate = LocalDate.parse(permit.startDate, dateFormatter),
                    endDate = LocalDate.parse(permit.endDate, dateFormatter),
                    partySize = permit.partySize,
                    enabled = permit.enabled,
                    selectedRiver = matchingRiver
                )
            } else {
                _uiState.value = _uiState.value.copy(
                    isLoadingPermit = false,
                    error = "Failed to load permit"
                )
            }
        }
    }

    fun selectRiver(river: RiverDto) {
        _uiState.value = _uiState.value.copy(
            selectedRiver = river,
            permitName = if (_uiState.value.permitName.isEmpty()) river.name else _uiState.value.permitName
        )
    }

    fun updatePermitName(name: String) {
        _uiState.value = _uiState.value.copy(permitName = name)
    }

    fun updateStartDate(date: LocalDate) {
        _uiState.value = _uiState.value.copy(startDate = date)
        // Ensure end date is after start date
        if (_uiState.value.endDate.isBefore(date)) {
            _uiState.value = _uiState.value.copy(endDate = date.plusMonths(1))
        }
    }

    fun updateEndDate(date: LocalDate) {
        _uiState.value = _uiState.value.copy(endDate = date)
    }

    fun updatePartySize(count: Int) {
        _uiState.value = _uiState.value.copy(partySize = count.coerceIn(1, 50))
    }

    fun updateEnabled(enabled: Boolean) {
        _uiState.value = _uiState.value.copy(enabled = enabled)
    }

    fun savePermit() {
        val state = _uiState.value

        // Validate
        if (state.selectedRiver == null) {
            _uiState.value = state.copy(error = "Please select a river")
            return
        }
        if (state.permitName.isBlank()) {
            _uiState.value = state.copy(error = "Please enter a permit name")
            return
        }
        if (state.endDate.isBefore(state.startDate)) {
            _uiState.value = state.copy(error = "End date must be after start date")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            val result = if (state.isEditMode && state.editPermitId != null) {
                // Update existing permit
                permitRepository.updatePermit(
                    permitId = state.editPermitId,
                    name = state.permitName,
                    facilityId = state.selectedRiver.facilityId,
                    startDate = state.startDate.format(dateFormatter),
                    endDate = state.endDate.format(dateFormatter),
                    partySize = state.partySize,
                    enabled = state.enabled
                )
            } else {
                // Create new permit
                permitRepository.createPermit(
                    name = state.permitName,
                    facilityId = state.selectedRiver.facilityId,
                    startDate = state.startDate.format(dateFormatter),
                    endDate = state.endDate.format(dateFormatter),
                    partySize = state.partySize
                ).let { createResult ->
                    when (createResult) {
                        is Result.Success -> Result.Success(Unit)
                        is Result.Error -> Result.Error(createResult.exception)
                        is Result.Loading -> Result.Loading
                    }
                }
            }

            when (result) {
                is Result.Success -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        isSuccess = true
                    )
                }
                is Result.Error -> {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = if (state.isEditMode) "Failed to update permit" else "Failed to create permit"
                    )
                }
                is Result.Loading -> {}
            }
        }
    }

    // Keep old method for compatibility
    fun createPermit() = savePermit()

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}
