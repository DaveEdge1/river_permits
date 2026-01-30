package com.riverpermits.app.ui.availability

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowLeft
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.riverpermits.app.data.remote.dto.AvailabilityRiverDto
import org.json.JSONArray

data class PermitAvailability(
    val date: String,
    val divisionId: String,
    val divisionName: String,
    val remaining: Int
)

data class RiverData(
    val permitName: String,
    val facilityId: String?,
    val permitCount: Int,
    val permits: List<PermitAvailability>,
    val hasMore: Boolean = false
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PermitAvailabilityScreen(
    totalCount: Int = 0,
    riverCount: Int = 0,
    riversJson: String? = null,
    onNavigateBack: () -> Unit,
    viewModel: PermitAvailabilityViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()

    // Determine if we should use notification data or fetch from API
    val hasNotificationData = !riversJson.isNullOrEmpty()

    // Parse notification data if available
    val notificationRivers = remember(riversJson) {
        if (hasNotificationData) parseRiversJson(riversJson) else emptyList()
    }

    // Fetch from API if no notification data
    LaunchedEffect(hasNotificationData) {
        if (!hasNotificationData) {
            viewModel.loadAvailability()
        }
    }

    // Convert API data to RiverData format
    val apiRivers = remember(uiState.rivers) {
        uiState.rivers.map { it.toRiverData() }
    }

    // Use notification data if available, otherwise use API data
    val rivers = if (hasNotificationData) notificationRivers else apiRivers
    val displayTotalCount = if (hasNotificationData) totalCount else uiState.totalCount
    val isLoading = !hasNotificationData && uiState.isLoading

    // Track which river is currently displayed
    var currentRiverIndex by remember { mutableIntStateOf(0) }

    // Reset index when rivers change
    LaunchedEffect(rivers.size) {
        if (currentRiverIndex >= rivers.size) {
            currentRiverIndex = 0
        }
    }

    // Get current river data
    val currentRiver = rivers.getOrNull(currentRiverIndex)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Permit Availability") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    if (!hasNotificationData) {
                        IconButton(
                            onClick = { viewModel.loadAvailability() },
                            enabled = !isLoading
                        ) {
                            Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    titleContentColor = MaterialTheme.colorScheme.onPrimary,
                    navigationIconContentColor = MaterialTheme.colorScheme.onPrimary,
                    actionIconContentColor = MaterialTheme.colorScheme.onPrimary
                )
            )
        }
    ) { paddingValues ->
        when {
            isLoading -> {
                // Loading state
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        CircularProgressIndicator()
                        Text(
                            text = "Checking permit availability...",
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }

            uiState.error != null && !hasNotificationData -> {
                // Error state
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp),
                        modifier = Modifier.padding(32.dp)
                    ) {
                        Text(
                            text = "Failed to load availability",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Text(
                            text = uiState.error ?: "",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.error,
                            textAlign = TextAlign.Center
                        )
                        Button(onClick = { viewModel.loadAvailability() }) {
                            Text("Try Again")
                        }
                    }
                }
            }

            rivers.isEmpty() -> {
                // No data available
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        modifier = Modifier.padding(32.dp)
                    ) {
                        Text(
                            text = "No permits available",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Text(
                            text = "No availability found for your configured permits and date ranges",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center
                        )
                        if (!hasNotificationData) {
                            Spacer(modifier = Modifier.height(8.dp))
                            OutlinedButton(onClick = { viewModel.loadAvailability() }) {
                                Icon(Icons.Default.Refresh, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Refresh")
                            }
                        }
                    }
                }
            }

            else -> {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 32.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Summary card
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(
                                containerColor = MaterialTheme.colorScheme.secondaryContainer
                            )
                        ) {
                            Text(
                                text = "$displayTotalCount permits available across ${rivers.size} river(s)",
                                style = MaterialTheme.typography.titleSmall,
                                color = MaterialTheme.colorScheme.onSecondaryContainer,
                                modifier = Modifier.padding(12.dp),
                                textAlign = TextAlign.Center
                            )
                        }
                    }

                    // River navigation (if multiple rivers)
                    if (rivers.size > 1) {
                        item {
                            RiverNavigator(
                                currentIndex = currentRiverIndex,
                                totalRivers = rivers.size,
                                riverName = currentRiver?.permitName ?: "",
                                onPrevious = {
                                    if (currentRiverIndex > 0) currentRiverIndex--
                                },
                                onNext = {
                                    if (currentRiverIndex < rivers.size - 1) currentRiverIndex++
                                }
                            )
                        }
                    }

                    // Header card with summary for current river
                    currentRiver?.let { river ->
                        item {
                            Card(
                                modifier = Modifier.fillMaxWidth(),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.primaryContainer
                                )
                            ) {
                                Column(
                                    modifier = Modifier.padding(16.dp)
                                ) {
                                    Text(
                                        text = river.permitName,
                                        style = MaterialTheme.typography.headlineSmall,
                                        fontWeight = FontWeight.Bold
                                    )
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Text(
                                        text = "${river.permitCount} permits available",
                                        style = MaterialTheme.typography.titleMedium,
                                        color = MaterialTheme.colorScheme.onPrimaryContainer
                                    )
                                }
                            }
                        }

                        // Recreation.gov link button
                        item {
                            val recreationGovUrl = buildRecreationGovUrl(river.facilityId, river.permitName)

                            OutlinedButton(
                                onClick = {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(recreationGovUrl))
                                    context.startActivity(intent)
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Icon(
                                    Icons.Default.OpenInNew,
                                    contentDescription = null,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("View on Recreation.gov")
                            }
                        }

                        // Group permits by division
                        val groupedByDivision = river.permits.groupBy { it.divisionName }

                        if (groupedByDivision.isNotEmpty()) {
                            item {
                                Text(
                                    text = "Available Dates",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(top = 8.dp)
                                )
                            }

                            groupedByDivision.forEach { (divisionName, permits) ->
                                item {
                                    Text(
                                        text = divisionName,
                                        style = MaterialTheme.typography.titleSmall,
                                        color = MaterialTheme.colorScheme.primary,
                                        modifier = Modifier.padding(top = 8.dp, bottom = 4.dp)
                                    )
                                }

                                items(permits.sortedBy { it.date }) { availability ->
                                    AvailabilityRow(availability)
                                }
                            }

                            // Show "and X more" message if there are additional permits not shown
                            if (river.hasMore) {
                                val additionalCount = river.permitCount - river.permits.size
                                item {
                                    Card(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(top = 8.dp),
                                        colors = CardDefaults.cardColors(
                                            containerColor = MaterialTheme.colorScheme.tertiaryContainer
                                        )
                                    ) {
                                        Text(
                                            text = "...and $additionalCount more dates available",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onTertiaryContainer,
                                            textAlign = TextAlign.Center,
                                            modifier = Modifier
                                                .fillMaxWidth()
                                                .padding(12.dp)
                                        )
                                    }
                                }
                            }
                        } else {
                            item {
                                Card(
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.surfaceVariant
                                    )
                                ) {
                                    Column(
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(24.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        Text(
                                            text = "Permit details not available",
                                            style = MaterialTheme.typography.bodyLarge
                                        )
                                        Text(
                                            text = "Check Recreation.gov for current availability",
                                            style = MaterialTheme.typography.bodyMedium,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun RiverNavigator(
    currentIndex: Int,
    totalRivers: Int,
    riverName: String,
    onPrevious: () -> Unit,
    onNext: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(
                onClick = onPrevious,
                enabled = currentIndex > 0
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.KeyboardArrowLeft,
                    contentDescription = "Previous river",
                    tint = if (currentIndex > 0)
                        MaterialTheme.colorScheme.onSecondaryContainer
                    else
                        MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.3f)
                )
            }

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = "River ${currentIndex + 1} of $totalRivers",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.7f)
                )
            }

            IconButton(
                onClick = onNext,
                enabled = currentIndex < totalRivers - 1
            ) {
                Icon(
                    Icons.AutoMirrored.Filled.KeyboardArrowRight,
                    contentDescription = "Next river",
                    tint = if (currentIndex < totalRivers - 1)
                        MaterialTheme.colorScheme.onSecondaryContainer
                    else
                        MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.3f)
                )
            }
        }
    }
}

@Composable
private fun AvailabilityRow(availability: PermitAvailability) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = formatDate(availability.date),
                style = MaterialTheme.typography.bodyLarge
            )
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = MaterialTheme.shapes.small
            ) {
                Text(
                    text = "${availability.remaining} available",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }
    }
}

// Extension function to convert API DTO to RiverData
private fun AvailabilityRiverDto.toRiverData(): RiverData {
    return RiverData(
        permitName = permitName,
        facilityId = facilityId,
        permitCount = permitCount,
        permits = permits.map { permit ->
            PermitAvailability(
                date = permit.date,
                divisionId = permit.divisionId,
                divisionName = permit.divisionName,
                remaining = permit.remaining
            )
        },
        hasMore = hasMore
    )
}

private fun parseRiversJson(json: String?): List<RiverData> {
    if (json.isNullOrEmpty()) return emptyList()

    return try {
        val jsonArray = JSONArray(json)
        val result = mutableListOf<RiverData>()

        for (i in 0 until jsonArray.length()) {
            val riverObj = jsonArray.getJSONObject(i)
            val permitsArray = riverObj.optJSONArray("permits")

            val permits = mutableListOf<PermitAvailability>()
            if (permitsArray != null) {
                for (j in 0 until permitsArray.length()) {
                    val permitObj = permitsArray.getJSONObject(j)
                    permits.add(
                        PermitAvailability(
                            date = permitObj.optString("date", ""),
                            divisionId = permitObj.optString("division_id", ""),
                            divisionName = permitObj.optString("division_name", "Unknown Section"),
                            remaining = permitObj.optInt("remaining", 0)
                        )
                    )
                }
            }

            result.add(
                RiverData(
                    permitName = riverObj.optString("permit_name", "Unknown River"),
                    facilityId = riverObj.optString("facility_id", "").ifEmpty { null },
                    permitCount = riverObj.optInt("permit_count", permits.size),
                    permits = permits,
                    hasMore = riverObj.optBoolean("has_more", false)
                )
            )
        }

        result
    } catch (e: Exception) {
        emptyList()
    }
}

private fun formatDate(dateStr: String): String {
    // Input format: 2026-03-08
    // Output format: Mar 8, 2026
    return try {
        val parts = dateStr.split("-")
        if (parts.size == 3) {
            val months = listOf("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
            val month = months[parts[1].toInt() - 1]
            val day = parts[2].toInt()
            val year = parts[0]
            "$month $day, $year"
        } else {
            dateStr
        }
    } catch (e: Exception) {
        dateStr
    }
}

private fun buildRecreationGovUrl(facilityId: String?, permitName: String): String {
    // If we have a facility ID, use it directly
    if (!facilityId.isNullOrEmpty()) {
        return "https://www.recreation.gov/permits/$facilityId"
    }

    // Otherwise, search for the permit name
    val searchQuery = permitName.replace(" ", "+")
    return "https://www.recreation.gov/search?q=$searchQuery"
}
