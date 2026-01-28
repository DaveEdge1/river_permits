package com.riverpermits.app.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "auth_prefs")

@Singleton
class TokenManager @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        private val ACCESS_TOKEN_KEY = stringPreferencesKey("access_token")
        private val REFRESH_TOKEN_KEY = stringPreferencesKey("refresh_token")
        private val USER_EMAIL_KEY = stringPreferencesKey("user_email")
        private val USER_ID_KEY = stringPreferencesKey("user_id")
        private val FCM_TOKEN_KEY = stringPreferencesKey("fcm_token")
    }

    val accessToken: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[ACCESS_TOKEN_KEY]
    }

    val refreshToken: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[REFRESH_TOKEN_KEY]
    }

    val userEmail: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[USER_EMAIL_KEY]
    }

    val userId: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[USER_ID_KEY]
    }

    val fcmToken: Flow<String?> = context.dataStore.data.map { prefs ->
        prefs[FCM_TOKEN_KEY]
    }

    val isLoggedIn: Flow<Boolean> = accessToken.map { !it.isNullOrEmpty() }

    suspend fun saveTokens(accessToken: String, refreshToken: String) {
        context.dataStore.edit { prefs ->
            prefs[ACCESS_TOKEN_KEY] = accessToken
            prefs[REFRESH_TOKEN_KEY] = refreshToken
        }
    }

    suspend fun saveUserInfo(userId: Int, email: String) {
        context.dataStore.edit { prefs ->
            prefs[USER_ID_KEY] = userId.toString()
            prefs[USER_EMAIL_KEY] = email
        }
    }

    suspend fun saveFcmToken(token: String) {
        context.dataStore.edit { prefs ->
            prefs[FCM_TOKEN_KEY] = token
        }
    }

    suspend fun clearAll() {
        context.dataStore.edit { prefs ->
            prefs.clear()
        }
    }
}
