package com.riverpermits.app.ui.addpermit

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.riverpermits.app.data.remote.dto.RiverDto
import java.time.LocalDate
import java.time.format.DateTimeFormatter

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddPermitScreen(
    onNavigateBack: () -> Unit,
    onPermitCreated: () -> Unit,
    viewModel: AddPermitViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val displayDateFormatter = remember { DateTimeFormatter.ofPattern("MMM d, yyyy") }

    // Handle success - navigate back
    LaunchedEffect(uiState.isSuccess) {
        if (uiState.isSuccess) {
            onPermitCreated()
        }
    }

    // Show error in snackbar
    LaunchedEffect(uiState.error) {
        uiState.error?.let { error ->
            snackbarHostState.showSnackbar(error)
            viewModel.clearError()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text("Add Permit") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        if (uiState.isLoadingRivers) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // River Selection
                item {
                    RiverSelector(
                        rivers = uiState.rivers,
                        selectedRiver = uiState.selectedRiver,
                        onRiverSelected = viewModel::selectRiver
                    )
                }

                // Permit Name
                item {
                    OutlinedTextField(
                        value = uiState.permitName,
                        onValueChange = viewModel::updatePermitName,
                        label = { Text("Permit Name") },
                        placeholder = { Text("e.g., Summer Trip 2026") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true
                    )
                }

                // Date Range
                item {
                    DateRangeSection(
                        startDate = uiState.startDate,
                        endDate = uiState.endDate,
                        onStartDateChange = viewModel::updateStartDate,
                        onEndDateChange = viewModel::updateEndDate,
                        dateFormatter = displayDateFormatter
                    )
                }

                // Party Size
                item {
                    PartySizeSection(
                        partySize = uiState.partySize,
                        onPartySizeChange = viewModel::updatePartySize
                    )
                }

                // Create Button
                item {
                    Spacer(modifier = Modifier.height(8.dp))
                    Button(
                        onClick = viewModel::createPermit,
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !uiState.isLoading && uiState.selectedRiver != null
                    ) {
                        if (uiState.isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Icon(Icons.Default.Add, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Create Permit")
                        }
                    }
                }

                // Bottom padding for navigation
                item {
                    Spacer(modifier = Modifier.height(32.dp))
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun RiverSelector(
    rivers: List<RiverDto>,
    selectedRiver: RiverDto?,
    onRiverSelected: (RiverDto) -> Unit
) {
    var expanded by remember { mutableStateOf(false) }

    Column {
        Text(
            text = "Select River",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        ExposedDropdownMenuBox(
            expanded = expanded,
            onExpandedChange = { expanded = it }
        ) {
            OutlinedTextField(
                value = selectedRiver?.name ?: "",
                onValueChange = {},
                readOnly = true,
                placeholder = { Text("Choose a river...") },
                trailingIcon = {
                    ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded)
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .menuAnchor()
            )

            ExposedDropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false }
            ) {
                rivers.forEach { river ->
                    DropdownMenuItem(
                        text = { Text(river.name) },
                        onClick = {
                            onRiverSelected(river)
                            expanded = false
                        },
                        leadingIcon = {
                            if (river == selectedRiver) {
                                Icon(Icons.Default.Check, contentDescription = null)
                            }
                        }
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DateRangeSection(
    startDate: LocalDate,
    endDate: LocalDate,
    onStartDateChange: (LocalDate) -> Unit,
    onEndDateChange: (LocalDate) -> Unit,
    dateFormatter: DateTimeFormatter
) {
    var showStartPicker by remember { mutableStateOf(false) }
    var showEndPicker by remember { mutableStateOf(false) }

    Column {
        Text(
            text = "Date Range",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Start Date
            OutlinedCard(
                modifier = Modifier
                    .weight(1f)
                    .clickable { showStartPicker = true }
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = "Start",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = startDate.format(dateFormatter),
                        style = MaterialTheme.typography.bodyLarge
                    )
                }
            }

            // End Date
            OutlinedCard(
                modifier = Modifier
                    .weight(1f)
                    .clickable { showEndPicker = true }
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(
                        text = "End",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = endDate.format(dateFormatter),
                        style = MaterialTheme.typography.bodyLarge
                    )
                }
            }
        }
    }

    // Date Pickers
    if (showStartPicker) {
        DatePickerDialog(
            initialDate = startDate,
            onDateSelected = {
                onStartDateChange(it)
                showStartPicker = false
            },
            onDismiss = { showStartPicker = false }
        )
    }

    if (showEndPicker) {
        DatePickerDialog(
            initialDate = endDate,
            onDateSelected = {
                onEndDateChange(it)
                showEndPicker = false
            },
            onDismiss = { showEndPicker = false }
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DatePickerDialog(
    initialDate: LocalDate,
    onDateSelected: (LocalDate) -> Unit,
    onDismiss: () -> Unit
) {
    val datePickerState = rememberDatePickerState(
        initialSelectedDateMillis = initialDate.toEpochDay() * 24 * 60 * 60 * 1000
    )

    DatePickerDialog(
        onDismissRequest = onDismiss,
        confirmButton = {
            TextButton(
                onClick = {
                    datePickerState.selectedDateMillis?.let { millis ->
                        val selectedDate = LocalDate.ofEpochDay(millis / (24 * 60 * 60 * 1000))
                        onDateSelected(selectedDate)
                    }
                }
            ) {
                Text("OK")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    ) {
        DatePicker(state = datePickerState)
    }
}

@Composable
private fun PartySizeSection(
    partySize: Int,
    onPartySizeChange: (Int) -> Unit
) {
    Column {
        Text(
            text = "Party Size",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 8.dp)
        )

        OutlinedTextField(
            value = partySize.toString(),
            onValueChange = { it.toIntOrNull()?.let(onPartySizeChange) },
            label = { Text("Number of people") },
            modifier = Modifier.fillMaxWidth(),
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
            singleLine = true
        )

        Text(
            text = "Minimum number of people in your party",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 4.dp)
        )
    }
}
