package com.riverpermits.app.ui.permit

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.riverpermits.app.R
import com.riverpermits.app.data.remote.dto.RiverDto

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PermitEditorScreen(
    permitId: Int?,
    viewModel: PermitEditorViewModel = hiltViewModel(),
    onNavigateBack: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    var showRiverPicker by remember { mutableStateOf(false) }

    // Navigate back on save success
    LaunchedEffect(uiState.saveSuccess) {
        if (uiState.saveSuccess) {
            onNavigateBack()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        if (uiState.isEditMode) stringResource(R.string.edit_permit)
                        else stringResource(R.string.add_permit)
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
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
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Permit name
                OutlinedTextField(
                    value = uiState.name,
                    onValueChange = viewModel::updateName,
                    label = { Text(stringResource(R.string.permit_name)) },
                    leadingIcon = { Icon(Icons.Default.Label, contentDescription = null) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )

                // River selection
                OutlinedTextField(
                    value = uiState.selectedRiver?.name ?: "",
                    onValueChange = {},
                    label = { Text(stringResource(R.string.select_river)) },
                    leadingIcon = { Icon(Icons.Default.Water, contentDescription = null) },
                    trailingIcon = { Icon(Icons.Default.ArrowDropDown, contentDescription = null) },
                    readOnly = true,
                    singleLine = true,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { showRiverPicker = true }
                )

                // Date range
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    OutlinedTextField(
                        value = uiState.startDate,
                        onValueChange = viewModel::updateStartDate,
                        label = { Text(stringResource(R.string.start_date)) },
                        placeholder = { Text("YYYY-MM-DD") },
                        singleLine = true,
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = uiState.endDate,
                        onValueChange = viewModel::updateEndDate,
                        label = { Text(stringResource(R.string.end_date)) },
                        placeholder = { Text("YYYY-MM-DD") },
                        singleLine = true,
                        modifier = Modifier.weight(1f)
                    )
                }

                // Party size
                Text(
                    text = stringResource(R.string.party_size),
                    style = MaterialTheme.typography.titleSmall
                )
                // Party size
                Column {
                    Text(
                        text = stringResource(R.string.party_size),
                        style = MaterialTheme.typography.bodySmall
                    )
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        IconButton(
                            onClick = { viewModel.updatePartySize(uiState.partySize - 1) }
                        ) {
                            Icon(Icons.Default.Remove, contentDescription = "Decrease")
                        }
                        Text(
                            text = uiState.partySize.toString(),
                            style = MaterialTheme.typography.titleLarge
                        )
                        IconButton(
                            onClick = { viewModel.updatePartySize(uiState.partySize + 1) }
                        ) {
                            Icon(Icons.Default.Add, contentDescription = "Increase")
                        }
                    }
                }

                // Enabled toggle (only for edit mode)
                if (uiState.isEditMode) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Monitoring enabled")
                        Switch(
                            checked = uiState.enabled,
                            onCheckedChange = viewModel::updateEnabled
                        )
                    }
                }

                // Error message
                if (uiState.error != null) {
                    Text(
                        text = uiState.error!!,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodyMedium
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // Save button
                Button(
                    onClick = viewModel::save,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                    enabled = !uiState.isSaving
                ) {
                    if (uiState.isSaving) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(24.dp),
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    } else {
                        Text(stringResource(R.string.save))
                    }
                }
            }
        }
    }

    // River picker dialog
    if (showRiverPicker) {
        RiverPickerDialog(
            rivers = uiState.rivers,
            selectedRiver = uiState.selectedRiver,
            onSelectRiver = {
                viewModel.selectRiver(it)
                showRiverPicker = false
            },
            onDismiss = { showRiverPicker = false }
        )
    }
}

@Composable
fun RiverPickerDialog(
    rivers: List<RiverDto>,
    selectedRiver: RiverDto?,
    onSelectRiver: (RiverDto) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Select River") },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 400.dp)
                    .verticalScroll(rememberScrollState())
            ) {
                rivers.forEach { river ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { onSelectRiver(river) }
                            .padding(vertical = 12.dp, horizontal = 8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = river.facilityId == selectedRiver?.facilityId,
                            onClick = { onSelectRiver(river) }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(river.name)
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
