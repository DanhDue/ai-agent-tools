import sys
import uuid
import re
import argparse

PROJECT_PATH = 'ios/Runner.xcodeproj/project.pbxproj'

def generate_id():
    return uuid.uuid4().hex[:24].upper()

def create_file_ref(file_id, name, path):
    return f'\t\t{file_id} /* {name} */ = {{isa = PBXFileReference; lastKnownFileType = text.xcconfig; name = "{name}"; path = "{path}"; sourceTree = "<group>"; }};'

def create_build_config(config_id, name, base_ref_id, bundle_id_suffix, mode):
    # Minimal Target Config
    
    swift_opt = 'SWIFT_OPTIMIZATION_LEVEL = "-Onone";' if mode == 'Debug' else 'SWIFT_OPTIMIZATION_LEVEL = "-O";'
    
    return f'''\t\t{config_id} /* {name} */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {base_ref_id};
\t\t\tbuildSettings = {{
\t\t\t\tASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCURRENT_PROJECT_VERSION = "$(FLUTTER_BUILD_NUMBER)";
\t\t\t\tENABLE_BITCODE = NO;
\t\t\t\tINFOPLIST_FILE = Runner/Info.plist;
\t\t\t\tLD_RUNPATH_SEARCH_PATHS = (
\t\t\t\t\t"$(inherited)",
\t\t\t\t\t"@executable_path/Frameworks",
\t\t\t\t);
\t\t\t\tPRODUCT_BUNDLE_IDENTIFIER = com.example.blocDigitalWallet;
\t\t\t\tPRODUCT_NAME = "$(TARGET_NAME)";
\t\t\t\tSWIFT_OBJC_BRIDGING_HEADER = "Runner/Runner-Bridging-Header.h";
\t\t\t\t{swift_opt}
\t\t\t\tSWIFT_VERSION = 5.0;
\t\t\t\tVERSIONING_SYSTEM = "apple-generic";
\t\t\t}};
\t\t\tname = {name};
\t\t}};'''

def create_project_build_config(config_id, name, base_ref_id, mode):
     # Project Config
     
     gcc_optimization = 'GCC_OPTIMIZATION_LEVEL = 0;' if mode == 'Debug' else '' 
     
     preprocess_defs = ''
     only_active_arch = ''
     debug_info_format = 'DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";'
     
     if mode == 'Debug':
         preprocess_defs = '''GCC_PREPROCESSOR_DEFINITIONS = (
\t\t\t\t\t"DEBUG=1",
\t\t\t\t\t"$(inherited)",
\t\t\t\t);'''
         only_active_arch = 'ONLY_ACTIVE_ARCH = YES;'
         debug_info_format = 'DEBUG_INFORMATION_FORMAT = dwarf;'
     
     validate_product = 'VALIDATE_PRODUCT = YES;'
     
     return f'''\t\t{config_id} /* {name} */ = {{
\t\t\tisa = XCBuildConfiguration;
\t\t\tbaseConfigurationReference = {base_ref_id};
\t\t\tbuildSettings = {{
\t\t\t\tALWAYS_SEARCH_USER_PATHS = NO;
\t\t\t\tASSETCATALOG_COMPILER_GENERATE_SWIFT_ASSET_SYMBOL_EXTENSIONS = YES;
\t\t\t\tCLANG_ANALYZER_NONNULL = YES;
\t\t\t\tCLANG_CXX_LANGUAGE_STANDARD = "gnu++0x";
\t\t\t\tCLANG_CXX_LIBRARY = "libc++";
\t\t\t\tCLANG_ENABLE_MODULES = YES;
\t\t\t\tCLANG_ENABLE_OBJC_ARC = YES;
\t\t\t\tCLANG_WARN_BLOCK_CAPTURE_AUTORELEASING = YES;
\t\t\t\tCLANG_WARN_BOOL_CONVERSION = YES;
\t\t\t\tCLANG_WARN_COMMA = YES;
\t\t\t\tCLANG_WARN_CONSTANT_CONVERSION = YES;
\t\t\t\tCLANG_WARN_DEPRECATED_OBJC_IMPLEMENTATIONS = YES;
\t\t\t\tCLANG_WARN_DIRECT_OBJC_ISA_USAGE = YES_ERROR;
\t\t\t\tCLANG_WARN_EMPTY_BODY = YES;
\t\t\t\tCLANG_WARN_ENUM_CONVERSION = YES;
\t\t\t\tCLANG_WARN_INFINITE_RECURSION = YES;
\t\t\t\tCLANG_WARN_INT_CONVERSION = YES;
\t\t\t\tCLANG_WARN_NON_LITERAL_NULL_CONVERSION = YES;
\t\t\t\tCLANG_WARN_OBJC_IMPLICIT_RETAIN_SELF = YES;
\t\t\t\tCLANG_WARN_OBJC_LITERAL_CONVERSION = YES;
\t\t\t\tCLANG_WARN_OBJC_ROOT_CLASS = YES_ERROR;
\t\t\t\tCLANG_WARN_RANGE_LOOP_ANALYSIS = YES;
\t\t\t\tCLANG_WARN_STRICT_PROTOTYPES = YES;
\t\t\t\tCLANG_WARN_SUSPICIOUS_MOVE = YES;
\t\t\t\tCLANG_WARN_UNREACHABLE_CODE = YES;
\t\t\t\tCLANG_WARN__DUPLICATE_METHOD_MATCH = YES;
\t\t\t\t"CODE_SIGN_IDENTITY[sdk=iphoneos*]" = "iPhone Developer";
\t\t\t\tCOPY_PHASE_STRIP = NO;
\t\t\t\t{debug_info_format}
\t\t\t\tENABLE_NS_ASSERTIONS = NO;
\t\t\t\tENABLE_STRICT_OBJC_MSGSEND = YES;
\t\t\t\tENABLE_USER_SCRIPT_SANDBOXING = NO;
\t\t\t\tGCC_C_LANGUAGE_STANDARD = gnu99;
\t\t\t\tGCC_NO_COMMON_BLOCKS = YES;
\t\t\t\t{gcc_optimization}
\t\t\t\t{preprocess_defs}
\t\t\t\tGCC_WARN_64_TO_32_BIT_CONVERSION = YES;
\t\t\t\tGCC_WARN_ABOUT_RETURN_TYPE = YES_ERROR;
\t\t\t\tGCC_WARN_UNDECLARED_SELECTOR = YES;
\t\t\t\tGCC_WARN_UNINITIALIZED_AUTOS = YES_AGGRESSIVE;
\t\t\t\tGCC_WARN_UNUSED_FUNCTION = YES;
\t\t\t\tGCC_WARN_UNUSED_VARIABLE = YES;
\t\t\t\tIPHONEOS_DEPLOYMENT_TARGET = 13.0;
\t\t\t\tMTL_ENABLE_DEBUG_INFO = NO;
\t\t\t\t{only_active_arch}
\t\t\t\tSDKROOT = iphoneos;
\t\t\t\tSUPPORTED_PLATFORMS = "iphoneos iphonesimulator";
\t\t\t\tSWIFT_COMPILATION_MODE = wholemodule;
\t\t\t\tSWIFT_OPTIMIZATION_LEVEL = "-O";
\t\t\t\tTARGETED_DEVICE_FAMILY = "1,2";
\t\t\t\t{validate_product}
\t\t\t}};
\t\t\tname = {name};
\t\t}};'''

def update_pbxproj():
    with open(PROJECT_PATH, 'r') as f:
        content = f.read()

    flavors = ['dev', 'stg', 'prd']
    modes = ['Debug', 'Release', 'Profile']
    
    new_file_refs = []
    new_build_configs = []
    
    created_configs = {} 

    parser = argparse.ArgumentParser()
    parser.add_argument('--app-name', required=True, help='Name of the application (e.g. Wallet)')
    args = parser.parse_args()
    
    app_name = args.app_name

    # 1. GENERATE FILE REFS
    file_ref_ids = {} 
    
    for extra in [f'{app_name}-defaults.xcconfig', f'{app_name}.xcconfig']:
        fid = generate_id()
        file_ref_ids[extra] = fid
        new_file_refs.append(create_file_ref(fid, extra, f'Flutter/{extra}'))

    for flavor in flavors:
        for mode in modes:
            fname = f'{mode}-{flavor}.xcconfig'
            fid = generate_id()
            file_ref_ids[fname] = fid
            new_file_refs.append(create_file_ref(fid, fname, f'Flutter/{fname}'))

    # 2. GENERATE BUILD CONFIGURATIONS
    for flavor in flavors:
        for mode in modes:
            config_name = f'{mode}-{flavor}'
            xcconfig_name = f'{config_name}.xcconfig'
            base_ref = file_ref_ids[xcconfig_name]
            
            # Project Config
            project_config_id = generate_id()
            new_build_configs.append(create_project_build_config(project_config_id, config_name, base_ref, mode))
            
            # Runner Target Config
            runner_config_id = generate_id()
            new_build_configs.append(create_build_config(runner_config_id, config_name, base_ref, f'.{flavor}', mode))

            if config_name not in created_configs: created_configs[config_name] = {}
            created_configs[config_name]['project'] = project_config_id
            created_configs[config_name]['runner'] = runner_config_id

    # 3. INSERT INTO FILE
    
    # Insert File Refs
    ref_marker = '/* Begin PBXFileReference section */'
    content = content.replace(ref_marker, ref_marker + '\n' + '\n'.join(new_file_refs))
    
    # Insert into Flutter Group
    group_regex = r'(9740EEB11CF90186004384FC /\* Flutter \*/ = \{[\s\S]*?children = \()([\s\S]*?)(\);)'
    
    def group_replacer(match):
        children_str = match.group(2)
        new_children = []
        for name, fid in file_ref_ids.items():
            new_children.append(f'\t\t\t\t{fid} /* {name} */,')
        return match.group(1) + children_str + '\n'.join(new_children) + '\n\t\t\t' + match.group(3)

    content = re.sub(group_regex, group_replacer, content)

    # Insert Build Configs
    config_marker = '/* Begin XCBuildConfiguration section */'
    content = content.replace(config_marker, config_marker + '\n' + '\n'.join(new_build_configs))
    
    # Update Configuration Lists
    project_list_regex = r'(97C146E91CF9000F007C117D /\* Build configuration list for PBXProject "Runner" \*/ = \{[\s\S]*?buildConfigurations = \()([\s\S]*?)(\);)'
    
    def project_list_replacer(match):
        existing = match.group(2)
        additions = []
        for flavor in flavors:
            for mode in modes:
                conf_name = f'{mode}-{flavor}'
                cid = created_configs[conf_name]['project']
                additions.append(f'\t\t\t\t{cid} /* {conf_name} */,')
        return match.group(1) + existing + '\n'.join(additions) + '\n\t\t\t' + match.group(3)
        
    content = re.sub(project_list_regex, project_list_replacer, content)
    
    runner_list_regex = r'(97C147051CF9000F007C117D /\* Build configuration list for PBXNativeTarget "Runner" \*/ = \{[\s\S]*?buildConfigurations = \()([\s\S]*?)(\);)'
    
    def runner_list_replacer(match):
        existing = match.group(2)
        additions = []
        for flavor in flavors:
            for mode in modes:
                conf_name = f'{mode}-{flavor}'
                cid = created_configs[conf_name]['runner']
                additions.append(f'\t\t\t\t{cid} /* {conf_name} */,')
        return match.group(1) + existing + '\n'.join(additions) + '\n\t\t\t' + match.group(3)

    content = re.sub(runner_list_regex, runner_list_replacer, content)

    with open(PROJECT_PATH, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    update_pbxproj()
    print("Project updated successfully")
