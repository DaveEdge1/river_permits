package com.riverpermits.app.ui.navigation

import android.util.Log
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.riverpermits.app.ui.admin.AdminScreen
import com.riverpermits.app.ui.auth.LoginScreen
import com.riverpermits.app.ui.auth.LoginViewModel
import com.riverpermits.app.ui.dashboard.DashboardScreen
import com.riverpermits.app.ui.settings.SettingsScreen

/**
 * Navigation routes
 */
sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object Settings : Screen("settings")
    data object Admin : Screen("admin")
}

/**
 * Main navigation graph
 */
@Composable
fun NavGraph(
    navController: NavHostController,
    startDestination: String = Screen.Login.route
) {
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
                    Log.d("NavGraph", "Navigating to Admin screen")
                    navController.navigate(Screen.Admin.route)
                }
            )
        }

        composable(Screen.Admin.route) {
            Log.d("NavGraph", "AdminScreen composable loading")
            AdminScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
