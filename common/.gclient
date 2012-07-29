solutions = [
  { "name"        : "src",
    "url"         : "http://git.chromium.org/chromium/src.git",
    "deps_file"   : ".DEPS.git",
    "managed"     : True,
    "custom_deps" : {
"src/third_party/WebKit/LayoutTests": None, # 158884 files, 1.37GB
"src/chrome_frame/tools/test/reference_build/chrome": None,
"src/chrome_frame/tools/test/reference_build/chrome_win": None,
"src/chrome/tools/test/reference_build/chrome": None,
"src/chrome/tools/test/reference_build/chrome_linux": None,
"src/chrome/tools/test/reference_build/chrome_mac": None,
"src/chrome/tools/test/reference_build/chrome_win": None,    
    },
    "safesync_url": "",
  },
]
