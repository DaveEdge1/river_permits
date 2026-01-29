package com.riverpermits.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.riverpermits.app.ui.auth.LoginScreen
import com.riverpermits.app.ui.dashboard.DashboardScreen
import com.riverpermits.app.ui.permit.PermitEditorScreen
import com.riverpermits.app.ui.settings.SettingsScreen
import com.riverpermits.app.ui.notifications.NotificationsScreen

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object PermitEditor : Screen("permit_editor?permitId={permitId}") {
        fun createRoute(permitId: Int? = null): String {
            return if (permitId != null) {
                "permit_editor?permitId=$permitId"
            } else {
                "permit_editor"
            }
        }
    }
    data object Settings : Screen("settings")
    data object Notifications : Screen("notifications")
}

@Composable
fun NavGraph(
    navController: NavHostController,
    isLoggedIn: Boolean
) {
    val startDestination = if (isLoggedIn) Screen.Dashboard.route else Screen.Login.route

    // Navigate to login when logged out
    LaunchedEffect(isLoggedIn) {
        if (!isLoggedIn) {
            navController.navigate(Screen.Login.route) {
                popUpTo(0) { inclusive = true }
            }
        }
    }

    NavHost(
        navController = navController,
        startDestination = startDestination
    ) {
        // Login Screen
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                }
            )
        }

        // Dashboard Screen
        composable(Screen.Dashboard.route) {
            DashboardScreen(
                onAddPermit = {
                    navController.navigate(Screen.PermitEditor.createRoute())
                },
                onEditPermit = { permitId ->
                    navController.navigate(Screen.PermitEditor.createRoute(permitId))
                },
                onOpenSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onOpenNotifications = {
                    navController.navigate(Screen.Notifications.route)
                }
            )
        }

        // Permit Editor Screen
        composable(
            route = Screen.PermitEditor.route,
            arguments = listOf(
                navArgument("permitId") {
                    type = NavType.IntType
                    defaultValue = -1
                }
            )
        ) { backStackEntry ->
            val permitId = backStackEntry.arguments?.getInt("permitId") ?: -1
            PermitEditorScreen(
                permitId = if (permitId == -1) null else permitId,
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }

        // Settings Screen
        composable(Screen.Settings.route) {
            SettingsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                }
            )
        }

        // Notifications Screen
        composable(Screen.Notifications.route) {
            NotificationsScreen(
                onNavigateBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
