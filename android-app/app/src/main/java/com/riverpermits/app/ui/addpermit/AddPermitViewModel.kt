package com.riverpermits.app.ui.addpermit

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
    val minPeople: Int = 1,
    val maxPeople: Int = 15,
    val isLoading: Boolean = false,
    val isLoadingRivers: Boolean = false,
    val error: String? = null,
    val isSuccess: Boolean = false
)

@HiltViewModel
class AddPermitViewModel @Inject constructor(
    private val permitRepository: PermitRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AddPermitUiState())
    val uiState: StateFlow<AddPermitUiState> = _uiState.asStateFlow()

    private val dateFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd")

    init {
        loadRivers()
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

    fun updateMinPeople(count: Int) {
        _uiState.value = _uiState.value.copy(minPeople = count.coerceIn(1, _uiState.value.maxPeople))
    }

    fun updateMaxPeople(count: Int) {
        _uiState.value = _uiState.value.copy(maxPeople = count.coerceIn(_uiState.value.minPeople, 50))
    }

    fun createPermit() {
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

            val result = permitRepository.createPermit(
                name = state.permitName,
                facilityId = state.selectedRiver.facilityId,
                startDate = state.startDate.format(dateFormatter),
                endDate = state.endDate.format(dateFormatter),
                minPeople = state.minPeople,
                maxPeople = state.maxPeople
            )

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
                        error = "Failed to create permit"
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
