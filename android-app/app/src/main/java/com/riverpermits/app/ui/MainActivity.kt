package com.riverpermits.app.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.riverpermits.app.ui.admin.AdminScreen
import com.riverpermits.app.ui.availability.PermitAvailabilityScreen
import com.riverpermits.app.ui.dashboard.DashboardScreen
import com.riverpermits.app.ui.login.LoginScreen
import com.riverpermits.app.ui.login.LoginViewModel
import com.riverpermits.app.ui.settings.SettingsScreen
import com.riverpermits.app.ui.theme.RiverPermitsTheme
import dagger.hilt.android.AndroidEntryPoint
import java.net.URLDecoder
import java.net.URLEncoder

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            Log.d("MainActivity", "Notification permission granted")
        } else {
            Log.d("MainActivity", "Notification permission denied")
        }
    }

    // Store notification data from intent
    private var notificationData: NotificationData? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Request notification permission on Android 13+
        askNotificationPermission()

        // Check if opened from notification
        notificationData = extractNotificationData(intent)

        setContent {
            RiverPermitsTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    RiverPermitsApp(notificationData)
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        // Handle notification tap when app is already running
        notificationData = extractNotificationData(intent)
        setIntent(intent)
    }

    private fun extractNotificationData(intent: Intent?): NotificationData? {
        if (intent == null) return null

        val permitName = intent.getStringExtra("permit_name")
        val permitCount = intent.getIntExtra("permit_count", 0)
        val permitsJson = intent.getStringExtra("permits_json")
        val facilityId = intent.getStringExtra("facility_id")

        return if (permitName != null && permitCount > 0) {
            Log.d("MainActivity", "Notification data received: $permitName, $permitCount permits")
            NotificationData(permitName, permitCount, permitsJson, facilityId)
        } else {
            null
        }
    }

    private fun askNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
                PackageManager.PERMISSION_GRANTED
            ) {
                requestPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
}

data class NotificationData(
    val permitName: String,
    val permitCount: Int,
    val permitsJson: String?,
    val facilityId: String?
)

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object Settings : Screen("settings")
    data object Admin : Screen("admin")
    data object PermitAvailability : Screen("permit_availability/{permitName}/{permitCount}?permitsJson={permitsJson}&facilityId={facilityId}") {
        fun createRoute(permitName: String, permitCount: Int, permitsJson: String?, facilityId: String?): String {
            val encodedName = URLEncoder.encode(permitName, "UTF-8")
            val encodedJson = permitsJson?.let { URLEncoder.encode(it, "UTF-8") } ?: ""
            val encodedFacilityId = facilityId ?: ""
            return "permit_availability/$encodedName/$permitCount?permitsJson=$encodedJson&facilityId=$encodedFacilityId"
        }
    }
}

@Composable
fun RiverPermitsApp(notificationData: NotificationData? = null) {
    val navController = rememberNavController()
    val loginViewModel: LoginViewModel = hiltViewModel()
    val uiState by loginViewModel.uiState.collectAsState()

    // Track if we've handled the notification navigation
    val hasNavigatedToNotification = remember { mutableStateOf(false) }

    // Determine start destination based on login state
    val startDestination = if (uiState.isLoggedIn) {
        Screen.Dashboard.route
    } else {
        Screen.Login.route
    }

    // Navigate to availability screen if opened from notification
    LaunchedEffect(notificationData, uiState.isLoggedIn) {
        if (notificationData != null && uiState.isLoggedIn && !hasNavigatedToNotification.value) {
            hasNavigatedToNotification.value = true
            val route = Screen.PermitAvailability.createRoute(
                permitName = notificationData.permitName,
                permitCount = notificationData.permitCount,
                permitsJson = notificationData.permitsJson,
                facilityId = notificationData.facilityId
            )
            navController.navigate(route)
        }
    }

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }

        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }

        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onNavigateToAdmin = {
                    Log.d("MainActivity", "Navigating to Admin screen")
                    navController.navigate(Screen.Admin.route)
                }
            )
        }

        composable(Screen.Admin.route) {
            Log.d("MainActivity", "AdminScreen composable loading")
            AdminScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            route = Screen.PermitAvailability.route,
            arguments = listOf(
                navArgument("permitName") { type = NavType.StringType },
                navArgument("permitCount") { type = NavType.IntType },
                navArgument("permitsJson") {
                    type = NavType.StringType
                    defaultValue = ""
                    nullable = true
                },
                navArgument("facilityId") {
                    type = NavType.StringType
                    defaultValue = ""
                    nullable = true
                }
            )
        ) { backStackEntry ->
            val permitName = backStackEntry.arguments?.getString("permitName")?.let {
                URLDecoder.decode(it, "UTF-8")
            } ?: ""
            val permitCount = backStackEntry.arguments?.getInt("permitCount") ?: 0
            val permitsJson = backStackEntry.arguments?.getString("permitsJson")?.let {
                if (it.isNotEmpty()) URLDecoder.decode(it, "UTF-8") else null
            }
            val facilityId = backStackEntry.arguments?.getString("facilityId")?.let {
                if (it.isNotEmpty()) it else null
            }

            PermitAvailabilityScreen(
                permitName = permitName,
                permitCount = permitCount,
                permitsJson = permitsJson,
                facilityId = facilityId,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
