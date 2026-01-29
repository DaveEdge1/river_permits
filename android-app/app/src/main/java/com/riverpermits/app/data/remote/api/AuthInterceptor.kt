package com.riverpermits.app.data.remote.api

import com.riverpermits.app.data.local.TokenManager
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenManager: TokenManager
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()

        // Skip auth for login and refresh endpoints
        val path = originalRequest.url.encodedPath
        if (path.contains("/login") || path.contains("/refresh")) {
            return chain.proceed(originalRequest)
        }

        // Get the access token
        val accessToken = runBlocking {
            tokenManager.accessToken.first()
        }

        // If no token, proceed without auth header
        if (accessToken.isNullOrEmpty()) {
            return chain.proceed(originalRequest)
        }

        // Add Authorization header
        val authenticatedRequest = originalRequest.newBuilder()
            .header("Authorization", "Bearer $accessToken")
            .build()

        return chain.proceed(authenticatedRequest)
    }
}
