pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
    plugins {
        id("com.android.application") version "8.5.0"
        id("org.jetbrains.kotlin.android") version "1.9.21"
        id("com.google.dagger.hilt.android") version "2.50"
        id("com.google.gms.google-services") version "4.4.0"
        id("com.google.devtools.ksp") version "1.9.21-1.0.15"
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "RiverPermits"
include(":app")
