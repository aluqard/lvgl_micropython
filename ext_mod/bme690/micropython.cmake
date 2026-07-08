# BME690 gas / environmental sensor (via BSEC 3.x) - MicroPython user C module
# (ESP32-S3 only)

add_library(usermod_bme690 INTERFACE)

set(BME690_INCLUDES
    ${CMAKE_CURRENT_LIST_DIR}/include
)

set(BME690_SOURCES
    ${CMAKE_CURRENT_LIST_DIR}/src/mod_bme690.c
    ${CMAKE_CURRENT_LIST_DIR}/src/bme690_i2c_bridge.c
    ${CMAKE_CURRENT_LIST_DIR}/src/bme69x.c
    ${CMAKE_CURRENT_LIST_DIR}/include/bme690_config.c
)

target_sources(usermod_bme690 INTERFACE ${BME690_SOURCES})
target_include_directories(usermod_bme690 INTERFACE ${BME690_INCLUDES})

# Bosch closed-source BSEC algorithm library (ESP32-S3 build).
add_library(bme690_bsec_prebuilt STATIC IMPORTED)
set_target_properties(bme690_bsec_prebuilt PROPERTIES
    IMPORTED_LOCATION ${CMAKE_CURRENT_LIST_DIR}/lib/libalgobsec.a)

target_link_libraries(usermod_bme690 INTERFACE bme690_bsec_prebuilt)

target_link_libraries(usermod INTERFACE usermod_bme690)
