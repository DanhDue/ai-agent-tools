---
name: android-api-integration
description: Generates a standardized Network Module, API Interface, Remote Data Source, Repository, UseCase, Models, and ViewModel updates for Android using the Hybrid Network Architecture and MVI Pattern.
---

# Android API Integration Skill

> [!IMPORTANT]
> **CHECK**: Ensure that `features/{feature}/src/main/kotlin` follows the MVI architecture provided in the mason templates. Models must be separated into `data/models` (with `Dto` suffix) and `domain/entities` (with `Entity` suffix, optional).

**Role**: Senior Android Architect Specialist.

**Objective**: Implement a complete end-to-end API integration for a specific feature, including Network Layer, Data Layer (Repository, Models), Domain Layer (UseCase, Entities), and Presentation Layer (ViewModel).

## Input Parameters

*   `FEATURE_NAME`: (e.g., "Payment", "Voucher", "CardManagement")
*   `BASE_URL`: (The specific API endpoint for this feature)
*   `API_ENDPOINTS`: (List of methods, paths, and return types)

## Implementation Steps

### 1. Network Layer (Hybrid Network Architecture)
If the network module does not exist, create it.
*   **Location**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/data/di/{FEATURE_NAME}NetworkModule.kt`
    *   Inject `Retrofit.Builder` from `:libraries:framework`.
    *   Provide a Singleton `Retrofit` instance (specific to the feature).
*   **API Interface**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/data/datasources/remote/{FEATURE_NAME}ApiService.kt`
    *   Return `NetworkResponse<T>`.
    *   Include `@Tag` with `FeatureConfig(appId = "...", featureName = "${FEATURE_NAME}")`.
*   **Remote Data Source**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/data/datasources/remote/{FEATURE_NAME}RemoteDataSource.kt`
    *   Inject the Api service.
    *   Implement methods to call API and return `NetworkResponse`. **NO TRY-CATCH**.

### 2. Data Layer Models (DTOs)
Create Data Transfer Objects for API requests/responses.
*   **Location**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/data/models/`
*   **Naming Rule**: Must end with `Dto` (e.g., `UserDto.kt`, `LoginResponseDto.kt`).
*   **Annotations**: Use `@Keep`, `@JsonClass(generateAdapter = true)`, and `@Json(name = "key")`.

### 3. Domain Layer Entities
Create pure Kotlin classes for business logic.
*   **Location**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/domain/entities/`
*   **Naming Rule**: Preferably end with `Entity` (e.g., `UserEntity.kt`) or keep it simple if it's a core model (e.g., `User.kt`), but **must not be the same as DTO**.
*   **Mappers**: Create generic extension functions in `data/mappers/` to map `Dto` -> `Entity`.

### 4. Repository Pattern
*   **Interface**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/domain/repository/{FEATURE_NAME}Repository.kt`
    *   Define abstract suspend functions returning `DataState<T>` (Domain Entity).
*   **Implementation**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/data/repository/{FEATURE_NAME}RepositoryImpl.kt`
    *   Inject `{FEATURE_NAME}RemoteDataSource`.
    *   Implement logic: Call RemoteDataSource -> Handle `NetworkResponse` -> Map DTO to Entity -> Return `DataState`.
*   **DI**: Update `data/di/{FEATURE_NAME}DataModule.kt`.
    *   Bind `RepositoryImpl` to `Repository` interface using `@Binds`.

### 5. UseCase
*   **Location**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/domain/usecase/Get{FEATURE_NAME}DataUseCase.kt` (or specific action name like `LoginUseCase.kt`).
*   **Implementation**: Single-responsibility class invoking the Repository.
*   **DI**: Update `domain/di/{FEATURE_NAME}DomainModule.kt`.
    *   Provide the UseCase (scoped to `@ViewModelScoped`).

### 6. Presentation Layer (ViewModel)
*   **Location**: `features/{feature_name_lowercase}/src/main/kotlin/com/danhdue/{feature_name_lowercase}/presentation/{screen}/{Screen}ViewModel.kt`
*   **Inheritance**: Must inherit from `MviViewModel<State, Action, Event>`.
*   **Injection**: Inject the UseCase.
*   **Logic**:
    *   Call UseCase in `safeLaunch`.
    *   Access state via `currentState` (or `uiState.value`).
    *   Update state via `reduce { copy(...) }`.
    *   Handle `DataState.Success` and `DataState.Error`.

## Constraint Rules

*   **Strict Naming**: `data/models` (plural), `domain/entities` (plural).
*   **Files**:
    *   Repo Impl: `{Name}RepositoryImpl` (NOT `Default...`).
    *   Data Models: `...Dto`.
*   **Architecture**: Follow Hybrid Network Architecture and MVI exactly.
*   **Error Handling**: Use `NetworkResponse` in Data Source and `DataState` in Repository/ViewModel.

## Example Usage

```markdown
Use the API Integration Skill to integrate:
- FEATURE_NAME: "Authentication"
- BASE_URL: "https://auth-service.com/"
- API_ENDPOINTS:
  - POST /login (body: LoginRequestDto) -> LoginResponseDto
```
