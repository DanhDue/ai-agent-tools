// Parse dart-defines from Flutter
val dartEnvironmentVariables =
    mutableMapOf(
        "DART_DEFINES_APP_NAME" to "Zeno",
        "DART_DEFINES_APP_ID_SUFFIX" to null,
        "DART_DEFINES_ENVIRONMENT" to "development",
    )

if (project.hasProperty("dart-defines")) {
    val dartDefinesStr = project.property("dart-defines").toString()
    dartDefinesStr.split(",").forEach { encoded ->
        val decoded = String(Base64.getDecoder().decode(encoded), Charsets.UTF_8)
        val pair = decoded.split("=")
        if (pair.size == 2) {
            dartEnvironmentVariables["DART_DEFINES_${pair[0]}"] = pair[1]
        }
    }
}

println("Dart defines: $dartEnvironmentVariables")

android {
    defaultConfig {
        // Dynamic application ID suffix from dart-defines
        applicationIdSuffix = dartEnvironmentVariables["DART_DEFINES_APP_ID_SUFFIX"]
        // Dynamic version name suffix
        versionNameSuffix = dartEnvironmentVariables["DART_DEFINES_APP_ID_SUFFIX"]?.let { ".$it" }
        // Dynamic app name from dart-defines
        resValue("string", "app_name", dartEnvironmentVariables["DART_DEFINES_APP_NAME"].toString())
    }

    flavorDimensions += "default"

    signingConfigs {
        create("development") {
            storeFile = rootProject.file("./../secureFiles/signing/debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
        create("production") {
            val keystorePropertiesFile = rootProject.file("./../secureFiles/signing/keystore.properties")
            if (keystorePropertiesFile.exists()) {
                println("Keystore properties file found: ${keystorePropertiesFile.absolutePath}")
                val keystoreProperties = Properties()
                keystoreProperties.load(FileInputStream(keystorePropertiesFile))
                storeFile = rootProject.file("./../secureFiles/signing/${keystoreProperties["storeFile"]}")
                storePassword = keystoreProperties["storePassword"] as String
                keyAlias = keystoreProperties["keyAlias"] as String
                keyPassword = keystoreProperties["keyPassword"] as String
            } else {
                println("⚠️  Keystore properties file not found, using debug keystore")
                storeFile = rootProject.file("./../secureFiles/signing/debug.keystore")
                storePassword = "android"
                keyAlias = "androiddebugkey"
                keyPassword = "android"
            }
        }
    }

    productFlavors {
        create("dev") {
            dimension = "default"
            signingConfig = signingConfigs.getByName("development")
        }
        create("stg") {
            dimension = "default"
            signingConfig = signingConfigs.getByName("development")
        }
        create("prd") {
            dimension = "default"
            signingConfig = signingConfigs.getByName("production")
        }
    }
}
