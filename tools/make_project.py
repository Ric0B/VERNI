#!/usr/bin/env python3
"""Writes WeeklyVerni.xcodeproj and the asset catalog. Sources in WeeklyVerni/ are picked up automatically."""
import json, math, struct, zlib, os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- asset catalog ----
assets = os.path.join(root, "WeeklyVerni", "Assets.xcassets")
os.makedirs(os.path.join(assets, "AppIcon.appiconset"), exist_ok=True)
os.makedirs(os.path.join(assets, "AccentColor.colorset"), exist_ok=True)
json.dump({"info": {"author": "xcode", "version": 1}}, open(os.path.join(assets, "Contents.json"), "w"), indent=2)
json.dump({"colors": [
    {"idiom": "universal", "color": {"color-space": "srgb", "components": {"red": "0.357", "green": "0.235", "blue": "1.000", "alpha": "1.000"}}},
    {"idiom": "universal", "appearances": [{"appearance": "luminosity", "value": "dark"}],
     "color": {"color-space": "srgb", "components": {"red": "0.627", "green": "0.541", "blue": "1.000", "alpha": "1.000"}}}],
    "info": {"author": "xcode", "version": 1}}, open(os.path.join(assets, "AccentColor.colorset", "Contents.json"), "w"), indent=2)

# ---- app icon: soft magenta / cyan / violet haze on ink, 1024 px ----
N = 1024
blobs = [(0.66, 0.30, 0.46, (255, 46, 126)), (0.30, 0.62, 0.44, (0, 191, 224)), (0.68, 0.74, 0.38, (123, 92, 255)), (0.36, 0.28, 0.22, (243, 198, 216))]
rows = []
for y in range(N):
    row = bytearray([0])
    for x in range(N):
        r, g, b = 23, 21, 29
        for bx, by, br, (cr, cg, cb) in blobs:
            d = math.hypot(x / N - bx, y / N - by) / br
            a = max(0.0, 1 - d) ** 1.6 * 0.95
            r += (cr - r) * a; g += (cg - g) * a; b += (cb - b) * a
        row += bytes((int(r), int(g), int(b)))
    rows.append(bytes(row))
raw = b"".join(rows)
def chunk(t, d): c = struct.pack(">I", len(d)) + t + d; return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
open(os.path.join(assets, "AppIcon.appiconset", "icon-1024.png"), "wb").write(png)
json.dump({"images": [{"filename": "icon-1024.png", "idiom": "universal", "platform": "ios", "size": "1024x1024"}],
           "info": {"author": "xcode", "version": 1}}, open(os.path.join(assets, "AppIcon.appiconset", "Contents.json"), "w"), indent=2)

# ---- project ----
proj = r'''// !$*UTF8*$!
{
	archiveVersion = 1;
	classes = {
	};
	objectVersion = 77;
	objects = {

/* Begin PBXFileReference section */
		A1000001 /* WeeklyVerni.app */ = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = WeeklyVerni.app; sourceTree = BUILT_PRODUCTS_DIR; };
/* End PBXFileReference section */

/* Begin PBXFileSystemSynchronizedRootGroup section */
		A1000002 /* WeeklyVerni */ = {
			isa = PBXFileSystemSynchronizedRootGroup;
			path = WeeklyVerni;
			sourceTree = "<group>";
		};
/* End PBXFileSystemSynchronizedRootGroup section */

/* Begin PBXFrameworksBuildPhase section */
		A1000003 /* Frameworks */ = {
			isa = PBXFrameworksBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXFrameworksBuildPhase section */

/* Begin PBXGroup section */
		A1000004 = {
			isa = PBXGroup;
			children = (
				A1000002 /* WeeklyVerni */,
				A1000005 /* Products */,
			);
			sourceTree = "<group>";
		};
		A1000005 /* Products */ = {
			isa = PBXGroup;
			children = (
				A1000001 /* WeeklyVerni.app */,
			);
			name = Products;
			sourceTree = "<group>";
		};
/* End PBXGroup section */

/* Begin PBXNativeTarget section */
		A1000006 /* WeeklyVerni */ = {
			isa = PBXNativeTarget;
			buildConfigurationList = A1000010 /* Build configuration list for PBXNativeTarget "WeeklyVerni" */;
			buildPhases = (
				A1000007 /* Sources */,
				A1000003 /* Frameworks */,
				A1000008 /* Resources */,
			);
			buildRules = (
			);
			dependencies = (
			);
			fileSystemSynchronizedGroups = (
				A1000002 /* WeeklyVerni */,
			);
			name = WeeklyVerni;
			packageProductDependencies = (
			);
			productName = WeeklyVerni;
			productReference = A1000001 /* WeeklyVerni.app */;
			productType = "com.apple.product-type.application";
		};
/* End PBXNativeTarget section */

/* Begin PBXProject section */
		A1000009 /* Project object */ = {
			isa = PBXProject;
			attributes = {
				BuildIndependentTargetsInParallel = 1;
				LastSwiftUpdateCheck = 1630;
				LastUpgradeCheck = 1630;
				TargetAttributes = {
					A1000006 = {
						CreatedOnToolsVersion = 16.3;
					};
				};
			};
			buildConfigurationList = A1000011 /* Build configuration list for PBXProject "WeeklyVerni" */;
			developmentRegion = en;
			hasScannedForEncodings = 0;
			knownRegions = (
				en,
				Base,
			);
			mainGroup = A1000004;
			minimizedProjectReferenceProxies = 1;
			preferredProjectObjectVersion = 77;
			productRefGroup = A1000005 /* Products */;
			projectDirPath = "";
			projectRoot = "";
			targets = (
				A1000006 /* WeeklyVerni */,
			);
		};
/* End PBXProject section */

/* Begin PBXResourcesBuildPhase section */
		A1000008 /* Resources */ = {
			isa = PBXResourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXResourcesBuildPhase section */

/* Begin PBXSourcesBuildPhase section */
		A1000007 /* Sources */ = {
			isa = PBXSourcesBuildPhase;
			buildActionMask = 2147483647;
			files = (
			);
			runOnlyForDeploymentPostprocessing = 0;
		};
/* End PBXSourcesBuildPhase section */

/* Begin XCBuildConfiguration section */
		A1000020 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = dwarf;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				ENABLE_TESTABILITY = YES;
				GCC_DYNAMIC_NO_PIC = NO;
				GCC_OPTIMIZATION_LEVEL = 0;
				GCC_PREPROCESSOR_DEFINITIONS = (
					"DEBUG=1",
					"$(inherited)",
				);
				IPHONEOS_DEPLOYMENT_TARGET = 17.0;
				MTL_ENABLE_DEBUG_INFO = INCLUDE_SOURCE;
				ONLY_ACTIVE_ARCH = YES;
				SDKROOT = iphoneos;
				SWIFT_ACTIVE_COMPILATION_CONDITIONS = "DEBUG $(inherited)";
				SWIFT_OPTIMIZATION_LEVEL = "-Onone";
			};
			name = Debug;
		};
		A1000021 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ALWAYS_SEARCH_USER_PATHS = NO;
				CLANG_ENABLE_MODULES = YES;
				CLANG_ENABLE_OBJC_ARC = YES;
				COPY_PHASE_STRIP = NO;
				DEBUG_INFORMATION_FORMAT = "dwarf-with-dsym";
				ENABLE_NS_ASSERTIONS = NO;
				ENABLE_STRICT_OBJC_MSGSEND = YES;
				IPHONEOS_DEPLOYMENT_TARGET = 17.0;
				MTL_ENABLE_DEBUG_INFO = NO;
				SDKROOT = iphoneos;
				SWIFT_COMPILATION_MODE = wholemodule;
				VALIDATE_PRODUCT = YES;
			};
			name = Release;
		};
		A1000022 /* Debug */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				ENABLE_PREVIEWS = YES;
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_KEY_CFBundleDisplayName = "Weekly VERNI";
				INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;
				INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES;
				INFOPLIST_KEY_UILaunchScreen_Generation = YES;
				INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone = UIInterfaceOrientationPortrait;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/Frameworks",
				);
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = com.verni.weekly;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = 1;
			};
			name = Debug;
		};
		A1000023 /* Release */ = {
			isa = XCBuildConfiguration;
			buildSettings = {
				ASSETCATALOG_COMPILER_APPICON_NAME = AppIcon;
				ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;
				CODE_SIGN_STYLE = Automatic;
				CURRENT_PROJECT_VERSION = 1;
				ENABLE_PREVIEWS = YES;
				GENERATE_INFOPLIST_FILE = YES;
				INFOPLIST_KEY_CFBundleDisplayName = "Weekly VERNI";
				INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES;
				INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES;
				INFOPLIST_KEY_UILaunchScreen_Generation = YES;
				INFOPLIST_KEY_UISupportedInterfaceOrientations_iPhone = UIInterfaceOrientationPortrait;
				LD_RUNPATH_SEARCH_PATHS = (
					"$(inherited)",
					"@executable_path/Frameworks",
				);
				MARKETING_VERSION = 1.0;
				PRODUCT_BUNDLE_IDENTIFIER = com.verni.weekly;
				PRODUCT_NAME = "$(TARGET_NAME)";
				SWIFT_EMIT_LOC_STRINGS = YES;
				SWIFT_VERSION = 5.0;
				TARGETED_DEVICE_FAMILY = 1;
			};
			name = Release;
		};
/* End XCBuildConfiguration section */

/* Begin XCConfigurationList section */
		A1000010 /* Build configuration list for PBXNativeTarget "WeeklyVerni" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1000022 /* Debug */,
				A1000023 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
		A1000011 /* Build configuration list for PBXProject "WeeklyVerni" */ = {
			isa = XCConfigurationList;
			buildConfigurations = (
				A1000020 /* Debug */,
				A1000021 /* Release */,
			);
			defaultConfigurationIsVisible = 0;
			defaultConfigurationName = Release;
		};
/* End XCConfigurationList section */
	};
	rootObject = A1000009 /* Project object */;
}
'''
os.makedirs(os.path.join(root, "WeeklyVerni.xcodeproj"), exist_ok=True)
open(os.path.join(root, "WeeklyVerni.xcodeproj", "project.pbxproj"), "w").write(proj)
print("project and assets written")
