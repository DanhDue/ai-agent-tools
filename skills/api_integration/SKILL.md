---
name: api_integration
description: Automate the end-to-end process of handling a new API request, from model generation to Data Source integration.
---

## SKILL MAPPING RULES

**IF** user provides:
- A CURL command or raw HTTP request details.
- A JSON response with a request to "handle", "integrate", or "implement" the API.
- A functional description (e.g., "Add Token Accounts API") along with endpoint details.
- A request to create a "client" or "datasource" for a specific API endpoint.

**THEN** follow this skill (`api_integration`):
1.  **Skip PLANNING** and `implementation_plan.md` creation.
2.  **Proceed directly to EXECUTION** following the steps below.

# API Integration Skill

This skill automates the process of implementing a new API request, ensuring all layers (models, clients, data sources, and DI) are correctly updated according to project standards.

> [!IMPORTANT]
> **Execute Immediately**: When this skill is requested, skip the `PLANNING` phase and `implementation_plan.md` creation. Proceed directly to `EXECUTION`. This skill requires zero verifications or confirmations before starting work.

> [!IMPORTANT]
> **Import Convention**: Always use **full package paths** (e.g., `import 'package:bloc_digital_wallet/core/network/app_uri.dart';`) instead of relative imports (e.g., `import '../../core/network/app_uri.dart';`).

> [!IMPORTANT]
> **DataSource Formatting**: Prefer single-line arrow syntax with wrapped return type:
> ```dart
> Future<Either<Failure, BaseResponseObject<List<TokenAccountObject>>>>
>     getTokenAccounts({required String address}) =>
>         safeApiCall(() => _client.getTokenAccounts(address));
> ```

## 1. Analysis Phase

1.  **Extract endpoint details**: Method, path, and parameters from the provided description or CURL.
2.  **Analyze JSON response**: Identify all objects and fields for model generation.

## 2. Model Generation

Use the `json_to_freezed_model` skill guidelines:
1.  **Create Freezed models** for all objects in `lib/features/{module}/data/models/`.
2.  **Apply strict naming**: All models must use `abstract class` and include `@JsonKey` for every field.
3.  **Snake Case mapping**: Ensure JSON snake_case fields are correctly mapped to camelCase Dart properties.

## 3. Network Layer Implementation

1.  **AppUri**: Add endpoint path constants to `lib/core/network/app_uri.dart`.
2.  **Retrofit Client**:
    - If the prompt specifies a client name (e.g., "token client"), use that: `token_client.dart`.
    - If no client name is specified, use the module name: `{module}_client.dart` (e.g., `wallet_client.dart`).
    - Create or update the module's client in `lib/features/{module}/data/datasources/`.
    - Use the `@RestApi()` and `@GET/@POST/etc.` annotations.
    - Wrap responses with `BaseResponseObject<T>`.
3.  **Dependency Injection**:
    - Register new clients in `lib/di/network_module.dart` using the `@singleton` or `@LazySingleton` annotation.
    - **CRITICAL**: Always provide the `baseUrl` explicitly when instantiating the client: `Client(dio, baseUrl: AppUri.service.buildAppUri()!)`. Avoid passing only `dio`.

> [!CRITICAL]
> **BaseUrl & Endpoint Path Analysis**
> 
> Before implementing any new Retrofit client, **ALWAYS analyze existing clients** to understand the baseUrl pattern:
> 
> **Step 1: Analyze the CURL/API endpoint**
> - Example: `GET https://api.example.com/api/v1/d3votion?word=test`
> - Full path: `/api/v1/d3votion`
> 
> **Step 2: Determine baseUrl in network_module.dart**
> - The `baseUrl` should include the **complete service path**
> - Example: `baseUrl: AppUri.d3Votion.buildAppUri()!` → `https://api.example.com/api/v1/d3votion`
> 
> **Step 3: Determine endpoint path in client**
> - If baseUrl already includes the full service path, endpoint should be **empty string** `''` or just the sub-path
> - **DO NOT duplicate the service path in the endpoint**
> 
> **Examples:**
> 
> ```dart
> // ✅ CORRECT - No path duplication
> // network_module.dart
> D3VotionClient(dio, baseUrl: AppUri.d3Votion.buildAppUri()!)
> // → baseUrl = "https://api.com/api/v1/d3votion"
> 
> // d3_votion_client.dart
> @GET('')  // Empty string, hits baseUrl directly
> Future<D3VotionResObject> getD3Votion(@Query("word") String word);
> // → Final URL: https://api.com/api/v1/d3votion?word=test ✅
> 
> // ✅ CORRECT - Sub-path added
> // network_module.dart
> TokenClient(dio, baseUrl: AppUri.tokens.buildAppUri()!)
> // → baseUrl = "https://api.com/api/v1/tokens"
> 
> // token_client.dart
> @GET(AppUri.accounts + UriPathParameters.address)  // Adds "/accounts/{address}"
> Future<BaseResponseObject<List<TokenAccountObject>>> getTokenAccounts(@Path("address") String address);
> // → Final URL: https://api.com/api/v1/tokens/accounts/{address} ✅
> 
> // ❌ WRONG - Path duplication
> // network_module.dart
> D3VotionClient(dio, baseUrl: AppUri.d3Votion.buildAppUri()!)
> // → baseUrl = "https://api.com/api/v1/d3votion"
> 
> // d3_votion_client.dart
> @GET('/${AppUri.d3Votion}')  // Adds "/d3votion" again!
> Future<D3VotionResObject> getD3Votion(@Query("word") String word);
> // → Final URL: https://api.com/api/v1/d3votion/d3votion ❌ WRONG!
> ```
> 
> **Decision Tree:**
> 1. Does the CURL hit the service root directly (e.g., `/api/v1/service`)?
>    - YES → Use empty string `''` as endpoint
>    - NO → Use the sub-path (e.g., `/accounts/{id}`)
> 2. Does the baseUrl already include the service name?
>    - YES → Do NOT add it again in the endpoint
>    - NO → Add it to the endpoint
> 
> **Always verify by comparing:**
> - CURL URL: `https://api.com/api/v1/d3votion?word=test`
> - baseUrl: `https://api.com/api/v1/d3votion`
> - Endpoint: `''`
> - Final URL: `https://api.com/api/v1/d3votion?word=test` ✅ Match!

## 4. Data Layer Integration

1.  **Remote Data Source Interface**: Add the new method returning `Future<Either<Failure, BaseResponseObject<T>>>`.
2.  **Remote Data Source Implementation**:
    - Ensure the class uses `with SafeCallApiMixin`.
    - Implement the method using `safeApiCall(() => client.method())`.

## 5. Verification & Finalization

1.  **Run Code Gen**: Execute `melos genAlls`.
2.  **Clean Analysis**: Run `fvm flutter analyze --no-fatal-infos` and ensure zero issues.
3.  **Finalization**: Create an `ai_integration_{retrofit_client_name}.md` artifact in the `.docs/` folder showing the changes and verification proof.
