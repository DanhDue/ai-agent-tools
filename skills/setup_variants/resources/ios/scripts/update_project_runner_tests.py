import uuid
import re

PROJECT_PATH = 'ios/Runner.xcodeproj/project.pbxproj'

def generate_id():
    return uuid.uuid4().hex[:24].upper()

def create_runner_tests_config(config_id, name, mode):
    # Base settings from Debug/Release concepts
    swift_conditions = 'SWIFT_ACTIVE_COMPILATION_CONDITIONS = DEBUG;' if mode == 'Debug' else ''
    swift_opt = 'SWIFT_OPTIMIZATION_LEVEL = "-Onone";' if mode == 'Debug' else ''
    
    return f'''\t\t{config_id} /* {name} */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbuildSettings = {{
\t\t\t\tBUNDLE_LOADER = "$(TEST_HOST)";
\t\t\t\tCODE_SIGN_STYLE = Automatic;
\t\t\t\tCURRENT_PROJECT_VERSION = 1;
\t\t\t\tGENERATE_INFOPLIST_FILE = YES;
\t\t\t\tMARKETING_VERSION = 1.0;
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.example.blocDigitalWallet.RunnerTests;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\t{swift_conditions}
\t\t\t\t{swift_opt}
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tTEST_HOST = "$(BUILT_PRODUCTS_DIR)/Runner.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/Runner";
\t\t\t}};
\t\t\tname = {name};
\t\t}};'''

def update_runner_tests():
    with open(PROJECT_PATH, 'r') as f:
        content = f.read()

    flavors = ['dev', 'stg', 'prd']
    modes = ['Debug', 'Release', 'Profile']
    
    new_configs = []
    created_ids = {}

    for flavor in flavors:
        for mode in modes:
            name = f'{mode}-{flavor}'
            cid = generate_id()
            created_ids[name] = cid
            new_configs.append(create_runner_tests_config(cid, name, mode))

    # Insert Configs
    config_marker = '/* Begin XCBuildConfiguration section */'
    content = content.replace(config_marker, config_marker + '\n' + '\n'.join(new_configs))

    # Add to RunnerTests Configuration List (331C8087294A63A400263BE5)
    list_regex = r'(331C8087294A63A400263BE5 /\* Build configuration list for PBXNativeTarget "RunnerTests" \*/ = \{[\s\S]*?buildConfigurations = \()([\s\S]*?)(\);)'
    
    def list_replacer(match):
        existing = match.group(2)
        additions = []
        for flavor in flavors:
            for mode in modes:
                name = f'{mode}-{flavor}'
                cid = created_ids[name]
                additions.append(f'\t\t\t\t{cid} /* {name} */,')
        return match.group(1) + existing + '\n'.join(additions) + '\n\t\t\t' + match.group(3)

    content = re.sub(list_regex, list_replacer, content)

    with open(PROJECT_PATH, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    update_runner_tests()
    print("RunnerTests configurations updated successfully")
