# BMV080 particulate matter sensor - MicroPython user C module (ESP32-S3 only)

add_library(usermod_bmv080 INTERFACE)

set(BMV080_INCLUDES
    ${CMAKE_CURRENT_LIST_DIR}/include
)

set(BMV080_SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/src/mod_bmv080.c
)

target_sources(usermod_bmv080 INTERFACE ${BMV080_SOURCES})
target_include_directories(usermod_bmv080 INTERFACE ${BMV080_INCLUDES})

# Bosch closed-source precompiled libraries (Xtensa ESP32-S3 build).
add_library(bmv080_prebuilt STATIC IMPORTED)
set_target_properties(bmv080_prebuilt PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_LIST_DIR}/lib/lib_bmv080.a)

add_library(bmv080_postproc_prebuilt STATIC IMPORTED)
set_target_properties(bmv080_postproc_prebuilt PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_LIST_DIR}/lib/lib_postProcessor.a)

# The two vendor archives reference each other, so let the linker resolve the
# cycle by grouping them.
target_link_libraries(usermod_bmv080 INTERFACE
    -Wl,--start-group
    bmv080_prebuilt
    bmv080_postproc_prebuilt
    -Wl,--end-group
)

target_link_libraries(usermod INTERFACE usermod_bmv080)
