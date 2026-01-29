package com.riverpermits.app.ui.availability

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.OpenInNew
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.json.JSONArray

data class PermitAvailability(
    val date: String,
    val divisionId: String,
    val divisionName: String,
    val remaining: Int
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PermitAvailabilityScreen(
    permitName: String,
    permitCount: Int,
    permitsJson: String?,
    facilityId: String?,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current

    // Parse the permits JSON
    val availabilities = parsePermitsJson(permitsJson)

    // Group by division name
    val groupedByDivision = availabilities.groupBy { it.divisionName }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Permit Availability") },
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
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 16.dp, bottom = 32.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Header card with summary
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
                            text = permitName,
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "$permitCount permits available",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }

            // Recreation.gov link button
            item {
                val recreationGovUrl = buildRecreationGovUrl(facilityId, permitName)

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

            // Availability by section
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

private fun parsePermitsJson(json: String?): List<PermitAvailability> {
    if (json.isNullOrEmpty()) return emptyList()

    return try {
        val jsonArray = JSONArray(json)
        val result = mutableListOf<PermitAvailability>()

        for (i in 0 until jsonArray.length()) {
            val obj = jsonArray.getJSONObject(i)
            result.add(
                PermitAvailability(
                    date = obj.optString("date", ""),
                    divisionId = obj.optString("division_id", ""),
                    divisionName = obj.optString("division_name", "Unknown Section"),
                    remaining = obj.optInt("remaining", 0)
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
