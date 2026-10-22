#include "constants/map_sections.h"
#include "constants/maps.h"
#include "constants/sndseq.h"

#include "fielddata/eventdata/zone_event.naix"
#include "fielddata/mapmatrix/map_matrix.naix"
#include "fielddata/script/scr_seq.naix"
#include "msgdata/msg.naix"

#include "encounter_tables_narc.h"
#include "map_header.h"

#ifdef _IN_MAP_HEADER_C

static const MapHeader sMapHeaders[] = {
    [MAP_EVERYWHERE] =
#include "data/maps/header_MAP_EVERYWHERE.h"
    ,
    [MAP_NOTHING] =
#include "data/maps/header_MAP_NOTHING.h"
    ,
    [MAP_UNION] =
#include "data/maps/header_MAP_UNION.h"
    ,
    [MAP_UNDERGROUND] =
#include "data/maps/header_MAP_UNDERGROUND.h"
    ,
    [MAP_WIFI_SINGLE_BATTLE_AREA] =
#include "data/maps/header_MAP_WIFI_SINGLE_BATTLE_AREA.h"
    ,
    [MAP_WIFI_MULTI_BATTLE_AREA] =
#include "data/maps/header_MAP_WIFI_MULTI_BATTLE_AREA.h"
    ,
    [MAP_BELLCHIME_TOWER] =
#include "data/maps/header_MAP_BELLCHIME_TOWER.h"
    ,
    [MAP_BURNED_TOWER_1F] =
#include "data/maps/header_MAP_BURNED_TOWER_1F.h"
    ,
    [MAP_RUINS_OF_ALPH_UNUSED] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_UNUSED.h"
    ,
    [MAP_ROUTE_1] =
#include "data/maps/header_MAP_ROUTE_1.h"
    ,
    [MAP_ROUTE_2] =
#include "data/maps/header_MAP_ROUTE_2.h"
    ,
    [MAP_ROUTE_3] =
#include "data/maps/header_MAP_ROUTE_3.h"
    ,
    [MAP_ROUTE_4] =
#include "data/maps/header_MAP_ROUTE_4.h"
    ,
    [MAP_ROUTE_5] =
#include "data/maps/header_MAP_ROUTE_5.h"
    ,
    [MAP_ROUTE_6] =
#include "data/maps/header_MAP_ROUTE_6.h"
    ,
    [MAP_ROUTE_7] =
#include "data/maps/header_MAP_ROUTE_7.h"
    ,
    [MAP_ROUTE_8] =
#include "data/maps/header_MAP_ROUTE_8.h"
    ,
    [MAP_ROUTE_9] =
#include "data/maps/header_MAP_ROUTE_9.h"
    ,
    [MAP_ROUTE_10] =
#include "data/maps/header_MAP_ROUTE_10.h"
    ,
    [MAP_ROUTE_11] =
#include "data/maps/header_MAP_ROUTE_11.h"
    ,
    [MAP_ROUTE_12] =
#include "data/maps/header_MAP_ROUTE_12.h"
    ,
    [MAP_ROUTE_13] =
#include "data/maps/header_MAP_ROUTE_13.h"
    ,
    [MAP_ROUTE_14] =
#include "data/maps/header_MAP_ROUTE_14.h"
    ,
    [MAP_ROUTE_15] =
#include "data/maps/header_MAP_ROUTE_15.h"
    ,
    [MAP_ROUTE_16] =
#include "data/maps/header_MAP_ROUTE_16.h"
    ,
    [MAP_ROUTE_17] =
#include "data/maps/header_MAP_ROUTE_17.h"
    ,
    [MAP_ROUTE_18] =
#include "data/maps/header_MAP_ROUTE_18.h"
    ,
    [MAP_ROUTE_22] =
#include "data/maps/header_MAP_ROUTE_22.h"
    ,
    [MAP_ROUTE_24] =
#include "data/maps/header_MAP_ROUTE_24.h"
    ,
    [MAP_ROUTE_25] =
#include "data/maps/header_MAP_ROUTE_25.h"
    ,
    [MAP_ROUTE_26] =
#include "data/maps/header_MAP_ROUTE_26.h"
    ,
    [MAP_ROUTE_27] =
#include "data/maps/header_MAP_ROUTE_27.h"
    ,
    [MAP_ROUTE_28] =
#include "data/maps/header_MAP_ROUTE_28.h"
    ,
    [MAP_ROUTE_29] =
#include "data/maps/header_MAP_ROUTE_29.h"
    ,
    [MAP_ROUTE_30] =
#include "data/maps/header_MAP_ROUTE_30.h"
    ,
    [MAP_ROUTE_31] =
#include "data/maps/header_MAP_ROUTE_31.h"
    ,
    [MAP_ROUTE_32] =
#include "data/maps/header_MAP_ROUTE_32.h"
    ,
    [MAP_ROUTE_33] =
#include "data/maps/header_MAP_ROUTE_33.h"
    ,
    [MAP_ROUTE_34] =
#include "data/maps/header_MAP_ROUTE_34.h"
    ,
    [MAP_ROUTE_35] =
#include "data/maps/header_MAP_ROUTE_35.h"
    ,
    [MAP_ROUTE_36] =
#include "data/maps/header_MAP_ROUTE_36.h"
    ,
    [MAP_ROUTE_37] =
#include "data/maps/header_MAP_ROUTE_37.h"
    ,
    [MAP_ROUTE_38] =
#include "data/maps/header_MAP_ROUTE_38.h"
    ,
    [MAP_ROUTE_39] =
#include "data/maps/header_MAP_ROUTE_39.h"
    ,
    [MAP_ROUTE_42] =
#include "data/maps/header_MAP_ROUTE_42.h"
    ,
    [MAP_ROUTE_43] =
#include "data/maps/header_MAP_ROUTE_43.h"
    ,
    [MAP_ROUTE_44] =
#include "data/maps/header_MAP_ROUTE_44.h"
    ,
    [MAP_ROUTE_45] =
#include "data/maps/header_MAP_ROUTE_45.h"
    ,
    [MAP_ROUTE_46] =
#include "data/maps/header_MAP_ROUTE_46.h"
    ,
    [MAP_PALLET] =
#include "data/maps/header_MAP_PALLET.h"
    ,
    [MAP_VIRIDIAN] =
#include "data/maps/header_MAP_VIRIDIAN.h"
    ,
    [MAP_PEWTER] =
#include "data/maps/header_MAP_PEWTER.h"
    ,
    [MAP_CERULEAN] =
#include "data/maps/header_MAP_CERULEAN.h"
    ,
    [MAP_LAVENDER] =
#include "data/maps/header_MAP_LAVENDER.h"
    ,
    [MAP_VERMILION] =
#include "data/maps/header_MAP_VERMILION.h"
    ,
    [MAP_CELADON] =
#include "data/maps/header_MAP_CELADON.h"
    ,
    [MAP_FUCHSIA] =
#include "data/maps/header_MAP_FUCHSIA.h"
    ,
    [MAP_CINNABAR_ISLAND] =
#include "data/maps/header_MAP_CINNABAR_ISLAND.h"
    ,
    [MAP_INDIGO_PLATEAU] =
#include "data/maps/header_MAP_INDIGO_PLATEAU.h"
    ,
    [MAP_SAFFRON] =
#include "data/maps/header_MAP_SAFFRON.h"
    ,
    [MAP_NEW_BARK] =
#include "data/maps/header_MAP_NEW_BARK.h"
    ,
    [MAP_NEW_BARK_ELMS_LAB_1F] =
#include "data/maps/header_MAP_NEW_BARK_ELMS_LAB_1F.h"
    ,
    [MAP_NEW_BARK_ELMS_LAB_2F] =
#include "data/maps/header_MAP_NEW_BARK_ELMS_LAB_2F.h"
    ,
    [MAP_NEW_BARK_PLAYER_HOUSE_1F] =
#include "data/maps/header_MAP_NEW_BARK_PLAYER_HOUSE_1F.h"
    ,
    [MAP_NEW_BARK_PLAYER_HOUSE_2F] =
#include "data/maps/header_MAP_NEW_BARK_PLAYER_HOUSE_2F.h"
    ,
    [MAP_NEW_BARK_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_NEW_BARK_SOUTHWEST_HOUSE.h"
    ,
    [MAP_NEW_BARK_RIVAL_HOUSE_1F] =
#include "data/maps/header_MAP_NEW_BARK_RIVAL_HOUSE_1F.h"
    ,
    [MAP_CHERRYGROVE] =
#include "data/maps/header_MAP_CHERRYGROVE.h"
    ,
    [MAP_CHERRYGROVE_POKEMART] =
#include "data/maps/header_MAP_CHERRYGROVE_POKEMART.h"
    ,
    [MAP_CHERRYGROVE_POKECENTER_1F] =
#include "data/maps/header_MAP_CHERRYGROVE_POKECENTER_1F.h"
    ,
    [MAP_CHERRYGROVE_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_CHERRYGROVE_SOUTHWEST_HOUSE.h"
    ,
    [MAP_CHERRYGROVE_GUIDE_GENT_HOUSE] =
#include "data/maps/header_MAP_CHERRYGROVE_GUIDE_GENT_HOUSE.h"
    ,
    [MAP_CHERRYGROVE_SOUTHEAST_HOUSE] =
#include "data/maps/header_MAP_CHERRYGROVE_SOUTHEAST_HOUSE.h"
    ,
    [MAP_VIOLET] =
#include "data/maps/header_MAP_VIOLET.h"
    ,
    [MAP_AZALEA] =
#include "data/maps/header_MAP_AZALEA.h"
    ,
    [MAP_CIANWOOD] =
#include "data/maps/header_MAP_CIANWOOD.h"
    ,
    [MAP_GOLDENROD] =
#include "data/maps/header_MAP_GOLDENROD.h"
    ,
    [MAP_OLIVINE] =
#include "data/maps/header_MAP_OLIVINE.h"
    ,
    [MAP_ECRUTEAK] =
#include "data/maps/header_MAP_ECRUTEAK.h"
    ,
    [MAP_ECRUTEAK_POKEMART] =
#include "data/maps/header_MAP_ECRUTEAK_POKEMART.h"
    ,
    [MAP_ECRUTEAK_GYM] =
#include "data/maps/header_MAP_ECRUTEAK_GYM.h"
    ,
    [MAP_ECRUTEAK_POKECENTER_1F] =
#include "data/maps/header_MAP_ECRUTEAK_POKECENTER_1F.h"
    ,
    [MAP_ECRUTEAK_UNUSED_HOUSE] =
#include "data/maps/header_MAP_ECRUTEAK_UNUSED_HOUSE.h"
    ,
    [MAP_ECRUTEAK_BELL_TOWER_BARRIER_STATION] =
#include "data/maps/header_MAP_ECRUTEAK_BELL_TOWER_BARRIER_STATION.h"
    ,
    [MAP_ECRUTEAK_DOWSING_MACHINE_HOUSE] =
#include "data/maps/header_MAP_ECRUTEAK_DOWSING_MACHINE_HOUSE.h"
    ,
    [MAP_ECRUTEAK_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_ECRUTEAK_SOUTHWEST_HOUSE.h"
    ,
    [MAP_ECRUTEAK_DANCE_THEATER] =
#include "data/maps/header_MAP_ECRUTEAK_DANCE_THEATER.h"
    ,
    [MAP_MAHOGANY] =
#include "data/maps/header_MAP_MAHOGANY.h"
    ,
    [MAP_LAKE_OF_RAGE] =
#include "data/maps/header_MAP_LAKE_OF_RAGE.h"
    ,
    [MAP_BLACKTHORN] =
#include "data/maps/header_MAP_BLACKTHORN.h"
    ,
    [MAP_MOUNT_SILVER] =
#include "data/maps/header_MAP_MOUNT_SILVER.h"
    ,
    [MAP_ROUTE_19] =
#include "data/maps/header_MAP_ROUTE_19.h"
    ,
    [MAP_ROUTE_20] =
#include "data/maps/header_MAP_ROUTE_20.h"
    ,
    [MAP_ROUTE_21] =
#include "data/maps/header_MAP_ROUTE_21.h"
    ,
    [MAP_ROUTE_40] =
#include "data/maps/header_MAP_ROUTE_40.h"
    ,
    [MAP_ROUTE_41] =
#include "data/maps/header_MAP_ROUTE_41.h"
    ,
    [MAP_NATIONAL_PARK] =
#include "data/maps/header_MAP_NATIONAL_PARK.h"
    ,
    [MAP_ROUTE_31_VIOLET_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_31_VIOLET_GATEHOUSE.h"
    ,
    [MAP_ROUTE_32_RUINS_OF_ALPH_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_32_RUINS_OF_ALPH_GATEHOUSE.h"
    ,
    [MAP_UNION_CAVE_1F] =
#include "data/maps/header_MAP_UNION_CAVE_1F.h"
    ,
    [MAP_AZALEA_ILEX_FOREST_GATEHOUSE] =
#include "data/maps/header_MAP_AZALEA_ILEX_FOREST_GATEHOUSE.h"
    ,
    [MAP_ROUTE_35_GOLDENROD_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_35_GOLDENROD_GATEHOUSE.h"
    ,
    [MAP_ROUTE_35_NATIONAL_PARK_POKEATHALON_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_35_NATIONAL_PARK_POKEATHALON_GATEHOUSE.h"
    ,
    [MAP_ROUTE_36_RUINS_OF_ALPH_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_36_RUINS_OF_ALPH_GATEHOUSE.h"
    ,
    [MAP_ROUTE_36_NATIONAL_PARK_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_36_NATIONAL_PARK_GATEHOUSE.h"
    ,
    [MAP_ECRUTEAK_UNUSED_GATEHOUSE] =
#include "data/maps/header_MAP_ECRUTEAK_UNUSED_GATEHOUSE.h"
    ,
    [MAP_DIGLETT_CAVE] =
#include "data/maps/header_MAP_DIGLETT_CAVE.h"
    ,
    [MAP_MOUNT_MOON] =
#include "data/maps/header_MAP_MOUNT_MOON.h"
    ,
    [MAP_ROCK_TUNNEL_1F] =
#include "data/maps/header_MAP_ROCK_TUNNEL_1F.h"
    ,
    [MAP_PAL_PARK] =
#include "data/maps/header_MAP_PAL_PARK.h"
    ,
    [MAP_SPROUT_TOWER_1F] =
#include "data/maps/header_MAP_SPROUT_TOWER_1F.h"
    ,
    [MAP_BELL_TOWER_1F] =
#include "data/maps/header_MAP_BELL_TOWER_1F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_1F] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_1F.h"
    ,
    [MAP_RUINS_OF_ALPH] =
#include "data/maps/header_MAP_RUINS_OF_ALPH.h"
    ,
    [MAP_SLOWPOKE_WELL_ENTRANCE] =
#include "data/maps/header_MAP_SLOWPOKE_WELL_ENTRANCE.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_1F] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_1F.h"
    ,
    [MAP_MAHOGANY_SOUVENIR_SHOP] =
#include "data/maps/header_MAP_MAHOGANY_SOUVENIR_SHOP.h"
    ,
    [MAP_ILEX_FOREST] =
#include "data/maps/header_MAP_ILEX_FOREST.h"
    ,
    [MAP_GOLDENROD_TUNNEL_1F] =
#include "data/maps/header_MAP_GOLDENROD_TUNNEL_1F.h"
    ,
    [MAP_MOUNT_MORTAR_1F_ENTRANCE] =
#include "data/maps/header_MAP_MOUNT_MORTAR_1F_ENTRANCE.h"
    ,
    [MAP_ICE_PATH_1F] =
#include "data/maps/header_MAP_ICE_PATH_1F.h"
    ,
    [MAP_WHIRL_ISLANDS_1F] =
#include "data/maps/header_MAP_WHIRL_ISLANDS_1F.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_1F] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_1F.h"
    ,
    [MAP_DARK_CAVE_ROUTE_45_SIDE] =
#include "data/maps/header_MAP_DARK_CAVE_ROUTE_45_SIDE.h"
    ,
    [MAP_VICTORY_ROAD_1F] =
#include "data/maps/header_MAP_VICTORY_ROAD_1F.h"
    ,
    [MAP_DRAGONS_DEN_ENTRANCE] =
#include "data/maps/header_MAP_DRAGONS_DEN_ENTRANCE.h"
    ,
    [MAP_TOHJO_FALLS] =
#include "data/maps/header_MAP_TOHJO_FALLS.h"
    ,
    [MAP_ROUTE_30_APRICORN_HOUSE] =
#include "data/maps/header_MAP_ROUTE_30_APRICORN_HOUSE.h"
    ,
    [MAP_ECRUTEAK_POKECENTER_UNUSED_1] =
#include "data/maps/header_MAP_ECRUTEAK_POKECENTER_UNUSED_1.h"
    ,
    [MAP_ECRUTEAK_POKECENTER_UNUSED_2] =
#include "data/maps/header_MAP_ECRUTEAK_POKECENTER_UNUSED_2.h"
    ,
    [MAP_ECRUTEAK_POKECENTER_UNUSED_3] =
#include "data/maps/header_MAP_ECRUTEAK_POKECENTER_UNUSED_3.h"
    ,
    [MAP_ECRUTEAK_POKECENTER_B1F] =
#include "data/maps/header_MAP_ECRUTEAK_POKECENTER_B1F.h"
    ,
    [MAP_ROUTE_42_ECRUTEAK_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_42_ECRUTEAK_GATEHOUSE.h"
    ,
    [MAP_MAHOGANY_EAST_HOUSE] =
#include "data/maps/header_MAP_MAHOGANY_EAST_HOUSE.h"
    ,
    [MAP_ROUTE_29_ROUTE_46_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_29_ROUTE_46_GATEHOUSE.h"
    ,
    [MAP_VIOLET_GYM] =
#include "data/maps/header_MAP_VIOLET_GYM.h"
    ,
    [MAP_AZALEA_GYM_ENTRANCE] =
#include "data/maps/header_MAP_AZALEA_GYM_ENTRANCE.h"
    ,
    [MAP_GOLDENROD_GYM] =
#include "data/maps/header_MAP_GOLDENROD_GYM.h"
    ,
    [MAP_OLIVINE_GYM] =
#include "data/maps/header_MAP_OLIVINE_GYM.h"
    ,
    [MAP_CIANWOOD_GYM] =
#include "data/maps/header_MAP_CIANWOOD_GYM.h"
    ,
    [MAP_MAHOGANY_GYM_LEADER_ROOM] =
#include "data/maps/header_MAP_MAHOGANY_GYM_LEADER_ROOM.h"
    ,
    [MAP_BLACKTHORN_GYM] =
#include "data/maps/header_MAP_BLACKTHORN_GYM.h"
    ,
    [MAP_ROUTE_43_MAHOGANY_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_43_MAHOGANY_GATEHOUSE.h"
    ,
    [MAP_ROUTE_30_MR_POKEMON_HOUSE] =
#include "data/maps/header_MAP_ROUTE_30_MR_POKEMON_HOUSE.h"
    ,
    [MAP_CHERRYGROVE_POKECENTER_B1F] =
#include "data/maps/header_MAP_CHERRYGROVE_POKECENTER_B1F.h"
    ,
    [MAP_CERULEAN_CAVE_1F] =
#include "data/maps/header_MAP_CERULEAN_CAVE_1F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_1F] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_1F.h"
    ,
    [MAP_VIRIDIAN_FOREST] =
#include "data/maps/header_MAP_VIRIDIAN_FOREST.h"
    ,
    [MAP_ROUTE_9_UNUSED] =
#include "data/maps/header_MAP_ROUTE_9_UNUSED.h"
    ,
    [MAP_VIOLET_ROUTE_36_GATEHOUSE] =
#include "data/maps/header_MAP_VIOLET_ROUTE_36_GATEHOUSE.h"
    ,
    [MAP_NATIONAL_PARK_UNUSED_GATEHOUSE] =
#include "data/maps/header_MAP_NATIONAL_PARK_UNUSED_GATEHOUSE.h"
    ,
    [MAP_ROUTE_47] =
#include "data/maps/header_MAP_ROUTE_47.h"
    ,
    [MAP_ROUTE_48] =
#include "data/maps/header_MAP_ROUTE_48.h"
    ,
    [MAP_UNION_CAVE_B1F] =
#include "data/maps/header_MAP_UNION_CAVE_B1F.h"
    ,
    [MAP_UNION_CAVE_B2F] =
#include "data/maps/header_MAP_UNION_CAVE_B2F.h"
    ,
    [MAP_SPROUT_TOWER_2F] =
#include "data/maps/header_MAP_SPROUT_TOWER_2F.h"
    ,
    [MAP_SPROUT_TOWER_3F] =
#include "data/maps/header_MAP_SPROUT_TOWER_3F.h"
    ,
    [MAP_VIOLET_POKEMART] =
#include "data/maps/header_MAP_VIOLET_POKEMART.h"
    ,
    [MAP_VIOLET_POKECENTER_1F] =
#include "data/maps/header_MAP_VIOLET_POKECENTER_1F.h"
    ,
    [MAP_VIOLET_POKEMON_SCHOOL] =
#include "data/maps/header_MAP_VIOLET_POKEMON_SCHOOL.h"
    ,
    [MAP_VIOLET_NORTHWEST_HOUSE] =
#include "data/maps/header_MAP_VIOLET_NORTHWEST_HOUSE.h"
    ,
    [MAP_VIOLET_UNUSED] =
#include "data/maps/header_MAP_VIOLET_UNUSED.h"
    ,
    [MAP_VIOLET_BELLSPROUT_ONYX_TRADE_HOUSE] =
#include "data/maps/header_MAP_VIOLET_BELLSPROUT_ONYX_TRADE_HOUSE.h"
    ,
    [MAP_AZALEA_CHARCOAL_KILN] =
#include "data/maps/header_MAP_AZALEA_CHARCOAL_KILN.h"
    ,
    [MAP_AZALEA_KURT_HOUSE] =
#include "data/maps/header_MAP_AZALEA_KURT_HOUSE.h"
    ,
    [MAP_AZALEA_POKEMART] =
#include "data/maps/header_MAP_AZALEA_POKEMART.h"
    ,
    [MAP_AZALEA_POKECENTER_1F] =
#include "data/maps/header_MAP_AZALEA_POKECENTER_1F.h"
    ,
    [MAP_VIOLET_POKECENTER_B1F] =
#include "data/maps/header_MAP_VIOLET_POKECENTER_B1F.h"
    ,
    [MAP_AZALEA_POKECENTER_B1F] =
#include "data/maps/header_MAP_AZALEA_POKECENTER_B1F.h"
    ,
    [MAP_ROUTE_32_POKECENTER_1F] =
#include "data/maps/header_MAP_ROUTE_32_POKECENTER_1F.h"
    ,
    [MAP_ROUTE_32_POKECENTER_B1F] =
#include "data/maps/header_MAP_ROUTE_32_POKECENTER_B1F.h"
    ,
    [MAP_ROUTE_34_ILEX_FOREST_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_34_ILEX_FOREST_GATEHOUSE.h"
    ,
    [MAP_ROUTE_38_ECRUTEAK_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_38_ECRUTEAK_GATEHOUSE.h"
    ,
    [MAP_SAFARI_ZONE_ENTRANCE_INTERIOR] =
#include "data/maps/header_MAP_SAFARI_ZONE_ENTRANCE_INTERIOR.h"
    ,
    [MAP_SAFARI_ZONE_GATE] =
#include "data/maps/header_MAP_SAFARI_ZONE_GATE.h"
    ,
    [MAP_ECRUTEAK_UNUSED_1] =
#include "data/maps/header_MAP_ECRUTEAK_UNUSED_1.h"
    ,
    [MAP_DARK_CAVE_ROUTE_31_SIDE] =
#include "data/maps/header_MAP_DARK_CAVE_ROUTE_31_SIDE.h"
    ,
    [MAP_SLOWPOKE_WELL_B1F] =
#include "data/maps/header_MAP_SLOWPOKE_WELL_B1F.h"
    ,
    [MAP_VICTORY_ROAD_2F] =
#include "data/maps/header_MAP_VICTORY_ROAD_2F.h"
    ,
    [MAP_VICTORY_ROAD_3F] =
#include "data/maps/header_MAP_VICTORY_ROAD_3F.h"
    ,
    [MAP_AZALEA_GYM] =
#include "data/maps/header_MAP_AZALEA_GYM.h"
    ,
    [MAP_SLOWPOKE_WELL_B2F] =
#include "data/maps/header_MAP_SLOWPOKE_WELL_B2F.h"
    ,
    [MAP_GOLDENROD_BIKE_SHOP] =
#include "data/maps/header_MAP_GOLDENROD_BIKE_SHOP.h"
    ,
    [MAP_GOLDENROD_GAME_CORNER_JP] =
#include "data/maps/header_MAP_GOLDENROD_GAME_CORNER_JP.h"
    ,
    [MAP_GOLDENROD_FLOWER_SHOP] =
#include "data/maps/header_MAP_GOLDENROD_FLOWER_SHOP.h"
    ,
    [MAP_GOLDENROD_POKECENTER_1F] =
#include "data/maps/header_MAP_GOLDENROD_POKECENTER_1F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_2F] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_2F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_3F] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_3F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_4F] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_4F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_5F] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_5F.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_OBSERVATION_DECK] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_OBSERVATION_DECK.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_1F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_1F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_2F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_2F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_3F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_3F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_4F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_4F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_5F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_5F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_6F] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_6F.h"
    ,
    [MAP_GOLDENROD_MAGNET_TRAIN_STATION_1F] =
#include "data/maps/header_MAP_GOLDENROD_MAGNET_TRAIN_STATION_1F.h"
    ,
    [MAP_GOLDENROD_MAGNET_TRAIN_STATION_2F] =
#include "data/maps/header_MAP_GOLDENROD_MAGNET_TRAIN_STATION_2F.h"
    ,
    [MAP_GOLDENROD_TUNNEL_B1F] =
#include "data/maps/header_MAP_GOLDENROD_TUNNEL_B1F.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_BASEMENT] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_BASEMENT.h"
    ,
    [MAP_GOLDENROD_TUNNEL_B2F] =
#include "data/maps/header_MAP_GOLDENROD_TUNNEL_B2F.h"
    ,
    [MAP_GOLDENROD_TUNNEL_WAREHOUSE] =
#include "data/maps/header_MAP_GOLDENROD_TUNNEL_WAREHOUSE.h"
    ,
    [MAP_GOLDENROD_BILLS_HOUSE] =
#include "data/maps/header_MAP_GOLDENROD_BILLS_HOUSE.h"
    ,
    [MAP_GOLDENROD_FRIENDSHIP_CHECKER_HOUSE] =
#include "data/maps/header_MAP_GOLDENROD_FRIENDSHIP_CHECKER_HOUSE.h"
    ,
    [MAP_GOLDENROD_NORTHEAST_HOUSE] =
#include "data/maps/header_MAP_GOLDENROD_NORTHEAST_HOUSE.h"
    ,
    [MAP_GOLDENROD_NAME_RATER_HOUSE] =
#include "data/maps/header_MAP_GOLDENROD_NAME_RATER_HOUSE.h"
    ,
    [MAP_GOLDENROD_GLOBAL_TERMINAL_1F] =
#include "data/maps/header_MAP_GOLDENROD_GLOBAL_TERMINAL_1F.h"
    ,
    [MAP_GOLDENROD_UNUSED_1] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_1.h"
    ,
    [MAP_GOLDENROD_UNUSED_2] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_2.h"
    ,
    [MAP_GOLDENROD_UNUSED_3] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_3.h"
    ,
    [MAP_GOLDENROD_UNUSED_4] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_4.h"
    ,
    [MAP_GOLDENROD_UNUSED_5] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_5.h"
    ,
    [MAP_GOLDENROD_UNUSED_6] =
#include "data/maps/header_MAP_GOLDENROD_UNUSED_6.h"
    ,
    [MAP_ROUTE_39_MOOMOO_FARM_HOUSE] =
#include "data/maps/header_MAP_ROUTE_39_MOOMOO_FARM_HOUSE.h"
    ,
    [MAP_ROUTE_39_MOOMOO_FARM_STABLE] =
#include "data/maps/header_MAP_ROUTE_39_MOOMOO_FARM_STABLE.h"
    ,
    [MAP_ECRUTEAK_BELL_TOWER_BARRIER_STATION_CORRIDOR] =
#include "data/maps/header_MAP_ECRUTEAK_BELL_TOWER_BARRIER_STATION_CORRIDOR.h"
    ,
    [MAP_BURNED_TOWER_B1F] =
#include "data/maps/header_MAP_BURNED_TOWER_B1F.h"
    ,
    [MAP_RUINS_OF_ALPH_UNUSED_2] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_UNUSED_2.h"
    ,
    [MAP_GOLDENROD_POKECENTER_B1F] =
#include "data/maps/header_MAP_GOLDENROD_POKECENTER_B1F.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_2F] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_2F.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_EXTERIOR] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_EXTERIOR.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_3F] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_3F.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_4F] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_4F.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_5F] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_5F.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_LIGHT_ROOM] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_LIGHT_ROOM.h"
    ,
    [MAP_OLIVINE_POKECENTER_1F] =
#include "data/maps/header_MAP_OLIVINE_POKECENTER_1F.h"
    ,
    [MAP_OLIVINE_POKEMART] =
#include "data/maps/header_MAP_OLIVINE_POKEMART.h"
    ,
    [MAP_OLIVINE_NORTH_HOUSE] =
#include "data/maps/header_MAP_OLIVINE_NORTH_HOUSE.h"
    ,
    [MAP_OLIVINE_NORTHEAST_HOUSE] =
#include "data/maps/header_MAP_OLIVINE_NORTHEAST_HOUSE.h"
    ,
    [MAP_OLIVINE_NORTHWEST_HOUSE] =
#include "data/maps/header_MAP_OLIVINE_NORTHWEST_HOUSE.h"
    ,
    [MAP_OLIVINE_CAFE] =
#include "data/maps/header_MAP_OLIVINE_CAFE.h"
    ,
    [MAP_CIANWOOD_KIRKS_HOUSE] =
#include "data/maps/header_MAP_CIANWOOD_KIRKS_HOUSE.h"
    ,
    [MAP_CIANWOOD_PHARMACY] =
#include "data/maps/header_MAP_CIANWOOD_PHARMACY.h"
    ,
    [MAP_CIANWOOD_CAMERONS_HOUSE] =
#include "data/maps/header_MAP_CIANWOOD_CAMERONS_HOUSE.h"
    ,
    [MAP_CIANWOOD_CENTRAL_HOUSE] =
#include "data/maps/header_MAP_CIANWOOD_CENTRAL_HOUSE.h"
    ,
    [MAP_CIANWOOD_POKECENTER_1F] =
#include "data/maps/header_MAP_CIANWOOD_POKECENTER_1F.h"
    ,
    [MAP_ICE_PATH_B1F] =
#include "data/maps/header_MAP_ICE_PATH_B1F.h"
    ,
    [MAP_ICE_PATH_B2F] =
#include "data/maps/header_MAP_ICE_PATH_B2F.h"
    ,
    [MAP_ICE_PATH_B3F] =
#include "data/maps/header_MAP_ICE_PATH_B3F.h"
    ,
    [MAP_SS_AQUA_OLIVINE_PORT_INTERIOR] =
#include "data/maps/header_MAP_SS_AQUA_OLIVINE_PORT_INTERIOR.h"
    ,
    [MAP_CIANWOOD_POKECENTER_B1F] =
#include "data/maps/header_MAP_CIANWOOD_POKECENTER_B1F.h"
    ,
    [MAP_WHIRL_ISLANDS_B1F] =
#include "data/maps/header_MAP_WHIRL_ISLANDS_B1F.h"
    ,
    [MAP_WHIRL_ISLANDS_B2F] =
#include "data/maps/header_MAP_WHIRL_ISLANDS_B2F.h"
    ,
    [MAP_WHIRL_ISLANDS_B3F_LUGIA_CAVE] =
#include "data/maps/header_MAP_WHIRL_ISLANDS_B3F_LUGIA_CAVE.h"
    ,
    [MAP_ROUTE_43_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_43_GATEHOUSE.h"
    ,
    [MAP_MAHOGANY_POKECENTER_1F] =
#include "data/maps/header_MAP_MAHOGANY_POKECENTER_1F.h"
    ,
    [MAP_TEAM_ROCKET_HEADQUARTERS_B1F] =
#include "data/maps/header_MAP_TEAM_ROCKET_HEADQUARTERS_B1F.h"
    ,
    [MAP_TEAM_ROCKET_HEADQUARTERS_B2F] =
#include "data/maps/header_MAP_TEAM_ROCKET_HEADQUARTERS_B2F.h"
    ,
    [MAP_TEAM_ROCKET_HEADQUARTERS_B3F] =
#include "data/maps/header_MAP_TEAM_ROCKET_HEADQUARTERS_B3F.h"
    ,
    [MAP_MOUNT_MORTAR_1F_BACK] =
#include "data/maps/header_MAP_MOUNT_MORTAR_1F_BACK.h"
    ,
    [MAP_MOUNT_MORTAR_2F] =
#include "data/maps/header_MAP_MOUNT_MORTAR_2F.h"
    ,
    [MAP_MOUNT_MORTAR_B1F] =
#include "data/maps/header_MAP_MOUNT_MORTAR_B1F.h"
    ,
    [MAP_DRAGONS_DEN] =
#include "data/maps/header_MAP_DRAGONS_DEN.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_1] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_1.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_2] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_2.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_3] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_3.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_4] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_4.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_5] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_5.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_6] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_6.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_7] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_7.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_8] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_8.h"
    ,
    [MAP_FIGHT_AREA_UNUSED_9] =
#include "data/maps/header_MAP_FIGHT_AREA_UNUSED_9.h"
    ,
    [MAP_BATTLE_PARK_UNUSED_1] =
#include "data/maps/header_MAP_BATTLE_PARK_UNUSED_1.h"
    ,
    [MAP_BATTLE_PARK_UNUSED_2] =
#include "data/maps/header_MAP_BATTLE_PARK_UNUSED_2.h"
    ,
    [MAP_BATTLE_TOWER] =
#include "data/maps/header_MAP_BATTLE_TOWER.h"
    ,
    [MAP_BATTLE_TOWER_ELEVATOR] =
#include "data/maps/header_MAP_BATTLE_TOWER_ELEVATOR.h"
    ,
    [MAP_BATTLE_TOWER_UNUSED_1] =
#include "data/maps/header_MAP_BATTLE_TOWER_UNUSED_1.h"
    ,
    [MAP_BATTLE_TOWER_UNUSED_2] =
#include "data/maps/header_MAP_BATTLE_TOWER_UNUSED_2.h"
    ,
    [MAP_BATTLE_TOWER_UNUSED_3] =
#include "data/maps/header_MAP_BATTLE_TOWER_UNUSED_3.h"
    ,
    [MAP_BATTLE_TOWER_UNUSED_4] =
#include "data/maps/header_MAP_BATTLE_TOWER_UNUSED_4.h"
    ,
    [MAP_BATTLE_TOWER_PARTNER_ROOM] =
#include "data/maps/header_MAP_BATTLE_TOWER_PARTNER_ROOM.h"
    ,
    [MAP_BATTLE_FRONTIER] =
#include "data/maps/header_MAP_BATTLE_FRONTIER.h"
    ,
    [MAP_BATTLE_FRONTIER_FRONTIER_ACCESS_GATEHOUSE] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_FRONTIER_ACCESS_GATEHOUSE.h"
    ,
    [MAP_BATTLE_FRONTIER_BATTLE_TOWER_UNUSED] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_BATTLE_TOWER_UNUSED.h"
    ,
    [MAP_BATTLE_FRONTIER_BATTLE_FACTORY] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_BATTLE_FACTORY.h"
    ,
    [MAP_BATTLE_FRONTIER_BATTLE_HALL] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_BATTLE_HALL.h"
    ,
    [MAP_BATTLE_FRONTIER_BATTLE_CASTLE] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_BATTLE_CASTLE.h"
    ,
    [MAP_BATTLE_FRONTIER_BATTLE_ARCADE] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_BATTLE_ARCADE.h"
    ,
    [MAP_CLIFF_EDGE_GATE] =
#include "data/maps/header_MAP_CLIFF_EDGE_GATE.h"
    ,
    [MAP_POKEATHLON_DOME] =
#include "data/maps/header_MAP_POKEATHLON_DOME.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_1F] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_1F.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_2F] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_2F.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_2F_ENTRANCE] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_2F_ENTRANCE.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_B1F_SOLIDARITY_ROOM] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_B1F_SOLIDARITY_ROOM.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_B1F_TRUST_ROOM] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_B1F_TRUST_ROOM.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_B1F_POTENTIAL_ROOM] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_B1F_POTENTIAL_ROOM.h"
    ,
    [MAP_POKEATHLON_DOME_INTERIOR_B1F_FRIENDSHIP_ROOM] =
#include "data/maps/header_MAP_POKEATHLON_DOME_INTERIOR_B1F_FRIENDSHIP_ROOM.h"
    ,
    [MAP_DRAGONS_DEN_SHRINE] =
#include "data/maps/header_MAP_DRAGONS_DEN_SHRINE.h"
    ,
    [MAP_BLACKTHORN_WEST_HOUSE] =
#include "data/maps/header_MAP_BLACKTHORN_WEST_HOUSE.h"
    ,
    [MAP_BLACKTHORN_EAST_HOUSE] =
#include "data/maps/header_MAP_BLACKTHORN_EAST_HOUSE.h"
    ,
    [MAP_BLACKTHORN_MOVE_TUTOR_HOUSE] =
#include "data/maps/header_MAP_BLACKTHORN_MOVE_TUTOR_HOUSE.h"
    ,
    [MAP_BLACKTHORN_POKEMART] =
#include "data/maps/header_MAP_BLACKTHORN_POKEMART.h"
    ,
    [MAP_BLACKTHORN_POKECENTER_1F] =
#include "data/maps/header_MAP_BLACKTHORN_POKECENTER_1F.h"
    ,
    [MAP_LAKE_OF_RAGE_HIDDEN_POWER_HOUSE] =
#include "data/maps/header_MAP_LAKE_OF_RAGE_HIDDEN_POWER_HOUSE.h"
    ,
    [MAP_LAKE_OF_RAGE_FISHING_GURU_HOUSE] =
#include "data/maps/header_MAP_LAKE_OF_RAGE_FISHING_GURU_HOUSE.h"
    ,
    [MAP_ROUTE_26_NORTH_HOUSE] =
#include "data/maps/header_MAP_ROUTE_26_NORTH_HOUSE.h"
    ,
    [MAP_ROUTE_26_WEEK_SIBLINGS_HOUSE] =
#include "data/maps/header_MAP_ROUTE_26_WEEK_SIBLINGS_HOUSE.h"
    ,
    [MAP_TOHJO_FALLS_HIDDEN_ROOM] =
#include "data/maps/header_MAP_TOHJO_FALLS_HIDDEN_ROOM.h"
    ,
    [MAP_ROUTE_22_POKEMON_LEAGUE_RECEPTION_GATE] =
#include "data/maps/header_MAP_ROUTE_22_POKEMON_LEAGUE_RECEPTION_GATE.h"
    ,
    [MAP_POKEMON_LEAGUE_ENTRANCE] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_ENTRANCE.h"
    ,
    [MAP_POKEMON_LEAGUE_WILL_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_WILL_ROOM.h"
    ,
    [MAP_POKEMON_LEAGUE_KOGA_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_KOGA_ROOM.h"
    ,
    [MAP_POKEMON_LEAGUE_BRUNO_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_BRUNO_ROOM.h"
    ,
    [MAP_POKEMON_LEAGUE_KAREN_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_KAREN_ROOM.h"
    ,
    [MAP_POKEMON_LEAGUE_LANCE_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_LANCE_ROOM.h"
    ,
    [MAP_POKEMON_LEAGUE_HALL_OF_FAME] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_HALL_OF_FAME.h"
    ,
    [MAP_SS_AQUA_1F] =
#include "data/maps/header_MAP_SS_AQUA_1F.h"
    ,
    [MAP_SS_AQUA_CAPTAIN_ROOM] =
#include "data/maps/header_MAP_SS_AQUA_CAPTAIN_ROOM.h"
    ,
    [MAP_SS_AQUA_1F_SOUTHEAST_ROOMS] =
#include "data/maps/header_MAP_SS_AQUA_1F_SOUTHEAST_ROOMS.h"
    ,
    [MAP_SS_AQUA_1F_SOUTHWEST_ROOMS] =
#include "data/maps/header_MAP_SS_AQUA_1F_SOUTHWEST_ROOMS.h"
    ,
    [MAP_SS_AQUA_1F_NORTHEAST_ROOMS] =
#include "data/maps/header_MAP_SS_AQUA_1F_NORTHEAST_ROOMS.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHEAST_ENTRANCE_FIRST_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHEAST_ENTRANCE_FIRST_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHEAST_HIDDEN_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHEAST_HIDDEN_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHEAST_ENTRANCE_FIRST_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHEAST_ENTRANCE_FIRST_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_UNDERGROUND_HALL] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_UNDERGROUND_HALL.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHWEST_ENTRANCE_FIRST_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHWEST_ENTRANCE_FIRST_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHWEST_HIDDEN_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHWEST_HIDDEN_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHWEST_ENTRANCE_FIRST_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHWEST_ENTRANCE_FIRST_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHWEST_HIDDEN_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHWEST_HIDDEN_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHEAST_HIDDEN_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHEAST_HIDDEN_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_RESEARCH_CENTER] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_RESEARCH_CENTER.h"
    ,
    [MAP_ROUTE_27_HOUSE] =
#include "data/maps/header_MAP_ROUTE_27_HOUSE.h"
    ,
    [MAP_RUINS_OF_ALPH_HALL_ENTRANCE] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_HALL_ENTRANCE.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHEAST_ENTRANCE_SECOND_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHEAST_ENTRANCE_SECOND_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHEAST_ENTRANCE_SECOND_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHEAST_ENTRANCE_SECOND_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_NORTHWEST_ENTRANCE_SECOND_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_NORTHWEST_ENTRANCE_SECOND_ROOM.h"
    ,
    [MAP_RUINS_OF_ALPH_SOUTHWEST_ENTRANCE_SECOND_ROOM] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_SOUTHWEST_ENTRANCE_SECOND_ROOM.h"
    ,
    [MAP_SS_AQUA_1F_NORTHWEST_ROOMS] =
#include "data/maps/header_MAP_SS_AQUA_1F_NORTHWEST_ROOMS.h"
    ,
    [MAP_SS_AQUA_B1F] =
#include "data/maps/header_MAP_SS_AQUA_B1F.h"
    ,
    [MAP_SS_AQUA_OLIVINE_PORT_EXTERIOR] =
#include "data/maps/header_MAP_SS_AQUA_OLIVINE_PORT_EXTERIOR.h"
    ,
    [MAP_ROUTE_34_DAYCARE] =
#include "data/maps/header_MAP_ROUTE_34_DAYCARE.h"
    ,
    [MAP_BELL_TOWER_2F] =
#include "data/maps/header_MAP_BELL_TOWER_2F.h"
    ,
    [MAP_BELL_TOWER_3F] =
#include "data/maps/header_MAP_BELL_TOWER_3F.h"
    ,
    [MAP_BELL_TOWER_4F] =
#include "data/maps/header_MAP_BELL_TOWER_4F.h"
    ,
    [MAP_BELL_TOWER_5F] =
#include "data/maps/header_MAP_BELL_TOWER_5F.h"
    ,
    [MAP_BELL_TOWER_6F] =
#include "data/maps/header_MAP_BELL_TOWER_6F.h"
    ,
    [MAP_BELL_TOWER_7F] =
#include "data/maps/header_MAP_BELL_TOWER_7F.h"
    ,
    [MAP_BELL_TOWER_8F] =
#include "data/maps/header_MAP_BELL_TOWER_8F.h"
    ,
    [MAP_BELL_TOWER_9F] =
#include "data/maps/header_MAP_BELL_TOWER_9F.h"
    ,
    [MAP_BELL_TOWER_ROOF] =
#include "data/maps/header_MAP_BELL_TOWER_ROOF.h"
    ,
    [MAP_BELL_TOWER_10F] =
#include "data/maps/header_MAP_BELL_TOWER_10F.h"
    ,
    [MAP_CLIFF_CAVE] =
#include "data/maps/header_MAP_CLIFF_CAVE.h"
    ,
    [MAP_SAFARI_ZONE_01] =
#include "data/maps/header_MAP_SAFARI_ZONE_01.h"
    ,
    [MAP_SAFARI_ZONE_02] =
#include "data/maps/header_MAP_SAFARI_ZONE_02.h"
    ,
    [MAP_SAFARI_ZONE_03] =
#include "data/maps/header_MAP_SAFARI_ZONE_03.h"
    ,
    [MAP_SAFARI_ZONE_04] =
#include "data/maps/header_MAP_SAFARI_ZONE_04.h"
    ,
    [MAP_SAFARI_ZONE_05] =
#include "data/maps/header_MAP_SAFARI_ZONE_05.h"
    ,
    [MAP_SAFARI_ZONE_06] =
#include "data/maps/header_MAP_SAFARI_ZONE_06.h"
    ,
    [MAP_SAFARI_ZONE_07] =
#include "data/maps/header_MAP_SAFARI_ZONE_07.h"
    ,
    [MAP_SAFARI_ZONE_08] =
#include "data/maps/header_MAP_SAFARI_ZONE_08.h"
    ,
    [MAP_SAFARI_ZONE_09] =
#include "data/maps/header_MAP_SAFARI_ZONE_09.h"
    ,
    [MAP_SAFARI_ZONE_10] =
#include "data/maps/header_MAP_SAFARI_ZONE_10.h"
    ,
    [MAP_SAFARI_ZONE_11] =
#include "data/maps/header_MAP_SAFARI_ZONE_11.h"
    ,
    [MAP_SAFARI_ZONE_12] =
#include "data/maps/header_MAP_SAFARI_ZONE_12.h"
    ,
    [MAP_SAFARI_ZONE_13] =
#include "data/maps/header_MAP_SAFARI_ZONE_13.h"
    ,
    [MAP_SAFARI_ZONE_14] =
#include "data/maps/header_MAP_SAFARI_ZONE_14.h"
    ,
    [MAP_SAFARI_ZONE_ENTRANCE_EXTERIOR] =
#include "data/maps/header_MAP_SAFARI_ZONE_ENTRANCE_EXTERIOR.h"
    ,
    [MAP_VERMILION_POKECENTER_1F] =
#include "data/maps/header_MAP_VERMILION_POKECENTER_1F.h"
    ,
    [MAP_VERMILION_POKECENTER_B1F] =
#include "data/maps/header_MAP_VERMILION_POKECENTER_B1F.h"
    ,
    [MAP_VERMILION_POKEMART] =
#include "data/maps/header_MAP_VERMILION_POKEMART.h"
    ,
    [MAP_VERMILION_FISHING_DUDE_HOUSE] =
#include "data/maps/header_MAP_VERMILION_FISHING_DUDE_HOUSE.h"
    ,
    [MAP_VERMILION_POKEMON_FAN_CLUB] =
#include "data/maps/header_MAP_VERMILION_POKEMON_FAN_CLUB.h"
    ,
    [MAP_VERMILION_CENTRAL_HOUSE] =
#include "data/maps/header_MAP_VERMILION_CENTRAL_HOUSE.h"
    ,
    [MAP_VERMILION_SOUTH_HOUSE] =
#include "data/maps/header_MAP_VERMILION_SOUTH_HOUSE.h"
    ,
    [MAP_VERMILION_GYM] =
#include "data/maps/header_MAP_VERMILION_GYM.h"
    ,
    [MAP_ROUTE_40_BATTLE_FRONTIER_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_40_BATTLE_FRONTIER_GATEHOUSE.h"
    ,
    [MAP_OLIVINE_POKECENTER_B1F] =
#include "data/maps/header_MAP_OLIVINE_POKECENTER_B1F.h"
    ,
    [MAP_MAHOGANY_POKECENTER_B1F] =
#include "data/maps/header_MAP_MAHOGANY_POKECENTER_B1F.h"
    ,
    [MAP_BLACKTHORN_POKECENTER_B1F] =
#include "data/maps/header_MAP_BLACKTHORN_POKECENTER_B1F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_1F] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_1F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_2F] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_2F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_3F] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_3F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_4F] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_4F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_5F] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_5F.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_ROOF] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_ROOF.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_1F] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_1F.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_2F] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_2F.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_3F] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_3F.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_ROOF] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_ROOF.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_ROOF_ROOM] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_ROOF_ROOM.h"
    ,
    [MAP_CELADON_GAME_CORNER_JP] =
#include "data/maps/header_MAP_CELADON_GAME_CORNER_JP.h"
    ,
    [MAP_CELADON_PRIZE_CORNER] =
#include "data/maps/header_MAP_CELADON_PRIZE_CORNER.h"
    ,
    [MAP_CELADON_RESTAURANT] =
#include "data/maps/header_MAP_CELADON_RESTAURANT.h"
    ,
    [MAP_NEW_BARK_RIVAL_HOUSE_2F] =
#include "data/maps/header_MAP_NEW_BARK_RIVAL_HOUSE_2F.h"
    ,
    [MAP_CIANWOOD_NORTH_HOUSE] =
#include "data/maps/header_MAP_CIANWOOD_NORTH_HOUSE.h"
    ,
    [MAP_SS_AQUA_VERMILION_PORT_INTERIOR] =
#include "data/maps/header_MAP_SS_AQUA_VERMILION_PORT_INTERIOR.h"
    ,
    [MAP_SS_AQUA_VERMILION_PORT_EXTERIOR] =
#include "data/maps/header_MAP_SS_AQUA_VERMILION_PORT_EXTERIOR.h"
    ,
    [MAP_ROUTE_10_SOUTH] =
#include "data/maps/header_MAP_ROUTE_10_SOUTH.h"
    ,
    [MAP_ROUTE_6_SAFFRON_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_6_SAFFRON_GATEHOUSE.h"
    ,
    [MAP_ROUTE_8_SAFFRON_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_8_SAFFRON_GATEHOUSE.h"
    ,
    [MAP_ROUTE_5_SAFFRON_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_5_SAFFRON_GATEHOUSE.h"
    ,
    [MAP_ROUTE_15_FUCHSIA_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_15_FUCHSIA_GATEHOUSE.h"
    ,
    [MAP_CELADON_POKECENTER_1F] =
#include "data/maps/header_MAP_CELADON_POKECENTER_1F.h"
    ,
    [MAP_CELADON_POKECENTER_B1F] =
#include "data/maps/header_MAP_CELADON_POKECENTER_B1F.h"
    ,
    [MAP_CELADON_GYM] =
#include "data/maps/header_MAP_CELADON_GYM.h"
    ,
    [MAP_MAHOGANY_GYM_ROOM_2] =
#include "data/maps/header_MAP_MAHOGANY_GYM_ROOM_2.h"
    ,
    [MAP_MAHOGANY_GYM_ROOM_1] =
#include "data/maps/header_MAP_MAHOGANY_GYM_ROOM_1.h"
    ,
    [MAP_SAFFRON_FIGHTING_DOJO] =
#include "data/maps/header_MAP_SAFFRON_FIGHTING_DOJO.h"
    ,
    [MAP_SAFFRON_MR_PSYCHIC_HOUSE] =
#include "data/maps/header_MAP_SAFFRON_MR_PSYCHIC_HOUSE.h"
    ,
    [MAP_SAFFRON_MAGNET_TRAIN_STATION_1F] =
#include "data/maps/header_MAP_SAFFRON_MAGNET_TRAIN_STATION_1F.h"
    ,
    [MAP_SAFFRON_MAGNET_TRAIN_STATION_2F] =
#include "data/maps/header_MAP_SAFFRON_MAGNET_TRAIN_STATION_2F.h"
    ,
    [MAP_SAFFRON_SILPH_CO_HQ] =
#include "data/maps/header_MAP_SAFFRON_SILPH_CO_HQ.h"
    ,
    [MAP_SAFFRON_SILPH_CO_ROTOM_ROOM] =
#include "data/maps/header_MAP_SAFFRON_SILPH_CO_ROTOM_ROOM.h"
    ,
    [MAP_SAFFRON_COPYCAT_HOUSE_1F] =
#include "data/maps/header_MAP_SAFFRON_COPYCAT_HOUSE_1F.h"
    ,
    [MAP_SAFFRON_COPYCAT_HOUSE_2F] =
#include "data/maps/header_MAP_SAFFRON_COPYCAT_HOUSE_2F.h"
    ,
    [MAP_SAFFRON_UNUSED] =
#include "data/maps/header_MAP_SAFFRON_UNUSED.h"
    ,
    [MAP_SAFFRON_POKECENTER_1F] =
#include "data/maps/header_MAP_SAFFRON_POKECENTER_1F.h"
    ,
    [MAP_SAFFRON_POKECENTER_2F] =
#include "data/maps/header_MAP_SAFFRON_POKECENTER_2F.h"
    ,
    [MAP_SAFFRON_POKEMART] =
#include "data/maps/header_MAP_SAFFRON_POKEMART.h"
    ,
    [MAP_SAFFRON_GYM] =
#include "data/maps/header_MAP_SAFFRON_GYM.h"
    ,
    [MAP_BATTLE_FRONTIER_FRONTIER_ACCESS] =
#include "data/maps/header_MAP_BATTLE_FRONTIER_FRONTIER_ACCESS.h"
    ,
    [MAP_GOLDENROD_GLOBAL_TERMINAL_2F] =
#include "data/maps/header_MAP_GOLDENROD_GLOBAL_TERMINAL_2F.h"
    ,
    [MAP_GOLDENROD_GLOBAL_TERMINAL_3F] =
#include "data/maps/header_MAP_GOLDENROD_GLOBAL_TERMINAL_3F.h"
    ,
    [MAP_ROUTE_2_EAST] =
#include "data/maps/header_MAP_ROUTE_2_EAST.h"
    ,
    [MAP_ROUTE_16_HOUSE] =
#include "data/maps/header_MAP_ROUTE_16_HOUSE.h"
    ,
    [MAP_ROUTE_20_UNUSED] =
#include "data/maps/header_MAP_ROUTE_20_UNUSED.h"
    ,
    [MAP_ROUTE_2_HOUSE] =
#include "data/maps/header_MAP_ROUTE_2_HOUSE.h"
    ,
    [MAP_ROUTE_2_SOUTHEAST_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_2_SOUTHEAST_GATEHOUSE.h"
    ,
    [MAP_ROUTE_2_VIRIDIAN_FOREST_SOUTH_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_2_VIRIDIAN_FOREST_SOUTH_GATEHOUSE.h"
    ,
    [MAP_ROUTE_2_VIRIDIAN_FOREST_NORTH_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_2_VIRIDIAN_FOREST_NORTH_GATEHOUSE.h"
    ,
    [MAP_ROUTE_16_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_16_GATEHOUSE.h"
    ,
    [MAP_ROUTE_16_EAST] =
#include "data/maps/header_MAP_ROUTE_16_EAST.h"
    ,
    [MAP_ROUTE_18_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_18_GATEHOUSE.h"
    ,
    [MAP_ROUTE_19_FUCHSIA_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_19_FUCHSIA_GATEHOUSE.h"
    ,
    [MAP_ROUTE_19_ROUTE_12_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_19_ROUTE_12_GATEHOUSE.h"
    ,
    [MAP_CERULEAN_POKEMART] =
#include "data/maps/header_MAP_CERULEAN_POKEMART.h"
    ,
    [MAP_CERULEAN_GYM] =
#include "data/maps/header_MAP_CERULEAN_GYM.h"
    ,
    [MAP_CERULEAN_POKECENTER_1F] =
#include "data/maps/header_MAP_CERULEAN_POKECENTER_1F.h"
    ,
    [MAP_CERULEAN_NORTH_HOUSE] =
#include "data/maps/header_MAP_CERULEAN_NORTH_HOUSE.h"
    ,
    [MAP_CERULEAN_EAST_HOUSE] =
#include "data/maps/header_MAP_CERULEAN_EAST_HOUSE.h"
    ,
    [MAP_CERULEAN_WEST_HOUSE] =
#include "data/maps/header_MAP_CERULEAN_WEST_HOUSE.h"
    ,
    [MAP_CERULEAN_BIKE_MANIAC_HOUSE] =
#include "data/maps/header_MAP_CERULEAN_BIKE_MANIAC_HOUSE.h"
    ,
    [MAP_LAVENDER_POKEMART] =
#include "data/maps/header_MAP_LAVENDER_POKEMART.h"
    ,
    [MAP_LAVENDER_POKECENTER_1F] =
#include "data/maps/header_MAP_LAVENDER_POKECENTER_1F.h"
    ,
    [MAP_LAVENDER_VOLUNTEER_POKEMON_HOUSE] =
#include "data/maps/header_MAP_LAVENDER_VOLUNTEER_POKEMON_HOUSE.h"
    ,
    [MAP_LAVENDER_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_LAVENDER_SOUTHWEST_HOUSE.h"
    ,
    [MAP_LAVENDER_NAME_RATER] =
#include "data/maps/header_MAP_LAVENDER_NAME_RATER.h"
    ,
    [MAP_LAVENDER_HOUSE_OF_MEMORIES] =
#include "data/maps/header_MAP_LAVENDER_HOUSE_OF_MEMORIES.h"
    ,
    [MAP_LAVENDER_RADIO_STATION] =
#include "data/maps/header_MAP_LAVENDER_RADIO_STATION.h"
    ,
    [MAP_ROUTE_25_SEA_COTTAGE] =
#include "data/maps/header_MAP_ROUTE_25_SEA_COTTAGE.h"
    ,
    [MAP_GOLDENROD_DEPARTMENT_STORE_ELEVATOR] =
#include "data/maps/header_MAP_GOLDENROD_DEPARTMENT_STORE_ELEVATOR.h"
    ,
    [MAP_CELADON_DEPARTMENT_STORE_ELEVATOR] =
#include "data/maps/header_MAP_CELADON_DEPARTMENT_STORE_ELEVATOR.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_LEFT_ELEVATOR] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_LEFT_ELEVATOR.h"
    ,
    [MAP_CELADON_CONDOMINIUMS_RIGHT_ELEVATOR] =
#include "data/maps/header_MAP_CELADON_CONDOMINIUMS_RIGHT_ELEVATOR.h"
    ,
    [MAP_SAFFRON_SILPH_CO_ELEVATOR] =
#include "data/maps/header_MAP_SAFFRON_SILPH_CO_ELEVATOR.h"
    ,
    [MAP_OLIVINE_LIGHTHOUSE_ELEVATOR] =
#include "data/maps/header_MAP_OLIVINE_LIGHTHOUSE_ELEVATOR.h"
    ,
    [MAP_GOLDENROD_RADIO_TOWER_ELEVATOR] =
#include "data/maps/header_MAP_GOLDENROD_RADIO_TOWER_ELEVATOR.h"
    ,
    [MAP_MOUNT_MOON_SQUARE_ENTRANCE] =
#include "data/maps/header_MAP_MOUNT_MOON_SQUARE_ENTRANCE.h"
    ,
    [MAP_MOUNT_MOON_SQUARE] =
#include "data/maps/header_MAP_MOUNT_MOON_SQUARE.h"
    ,
    [MAP_CERULEAN_CAVE_2F] =
#include "data/maps/header_MAP_CERULEAN_CAVE_2F.h"
    ,
    [MAP_CERULEAN_CAVE_B1F] =
#include "data/maps/header_MAP_CERULEAN_CAVE_B1F.h"
    ,
    [MAP_ROCK_TUNNEL_B1F] =
#include "data/maps/header_MAP_ROCK_TUNNEL_B1F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_B1F] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_B1F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_B2F] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_B2F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_B3F] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_B3F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_B4F] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_B4F.h"
    ,
    [MAP_SEAFOAM_ISLANDS_CINNABAR_GYM] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_CINNABAR_GYM.h"
    ,
    [MAP_SEAFOAM_ISLANDS_UNUSED] =
#include "data/maps/header_MAP_SEAFOAM_ISLANDS_UNUSED.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_UPPER_MOUNTAINSIDE] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_UPPER_MOUNTAINSIDE.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_LOWER_MOUNTAINSIDE] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_LOWER_MOUNTAINSIDE.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_EXPERT_BELT_CHAMBER] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_EXPERT_BELT_CHAMBER.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_MOLTRES_CHAMBER] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_MOLTRES_CHAMBER.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_2F] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_2F.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_3F] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_3F.h"
    ,
    [MAP_MOUNT_SILVER_CAVE_SUMMIT] =
#include "data/maps/header_MAP_MOUNT_SILVER_CAVE_SUMMIT.h"
    ,
    [MAP_ROUTE_10_POKECENTER_1F] =
#include "data/maps/header_MAP_ROUTE_10_POKECENTER_1F.h"
    ,
    [MAP_ROUTE_10_POWER_PLANT_REPAIRED] =
#include "data/maps/header_MAP_ROUTE_10_POWER_PLANT_REPAIRED.h"
    ,
    [MAP_ROUTE_5_UNUSED] =
#include "data/maps/header_MAP_ROUTE_5_UNUSED.h"
    ,
    [MAP_ROUTE_5_UNDERGROUND_PATH_GATE] =
#include "data/maps/header_MAP_ROUTE_5_UNDERGROUND_PATH_GATE.h"
    ,
    [MAP_ROUTE_6_UNDERGROUND_PATH_GATE] =
#include "data/maps/header_MAP_ROUTE_6_UNDERGROUND_PATH_GATE.h"
    ,
    [MAP_PEWTER_MUSEUM_OF_SCIENCE] =
#include "data/maps/header_MAP_PEWTER_MUSEUM_OF_SCIENCE.h"
    ,
    [MAP_PEWTER_NORTHEAST_HOUSE] =
#include "data/maps/header_MAP_PEWTER_NORTHEAST_HOUSE.h"
    ,
    [MAP_PEWTER_GYM] =
#include "data/maps/header_MAP_PEWTER_GYM.h"
    ,
    [MAP_PEWTER_POKEMART] =
#include "data/maps/header_MAP_PEWTER_POKEMART.h"
    ,
    [MAP_PEWTER_POKECENTER_1F] =
#include "data/maps/header_MAP_PEWTER_POKECENTER_1F.h"
    ,
    [MAP_PEWTER_POKECENTER_B1F] =
#include "data/maps/header_MAP_PEWTER_POKECENTER_B1F.h"
    ,
    [MAP_PEWTER_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_PEWTER_SOUTHWEST_HOUSE.h"
    ,
    [MAP_FUCHSIA_POKEMART] =
#include "data/maps/header_MAP_FUCHSIA_POKEMART.h"
    ,
    [MAP_FUCHSIA_PAL_PARK_ENTRANCE] =
#include "data/maps/header_MAP_FUCHSIA_PAL_PARK_ENTRANCE.h"
    ,
    [MAP_FUCHSIA_GYM] =
#include "data/maps/header_MAP_FUCHSIA_GYM.h"
    ,
    [MAP_FUCHSIA_SOUTHWEST_HOUSE] =
#include "data/maps/header_MAP_FUCHSIA_SOUTHWEST_HOUSE.h"
    ,
    [MAP_FUCHSIA_POKECENTER_1F] =
#include "data/maps/header_MAP_FUCHSIA_POKECENTER_1F.h"
    ,
    [MAP_FUCHSIA_SAFARI_ZONE_WARDEN_HOUSE] =
#include "data/maps/header_MAP_FUCHSIA_SAFARI_ZONE_WARDEN_HOUSE.h"
    ,
    [MAP_ROUTE_10_POKECENTER_B1F] =
#include "data/maps/header_MAP_ROUTE_10_POKECENTER_B1F.h"
    ,
    [MAP_FUCHSIA_POKECENTER_B1F] =
#include "data/maps/header_MAP_FUCHSIA_POKECENTER_B1F.h"
    ,
    [MAP_WHIRL_ISLANDS_B3F] =
#include "data/maps/header_MAP_WHIRL_ISLANDS_B3F.h"
    ,
    [MAP_NATIONAL_PARK_BUG_CATCHING_CONTEST] =
#include "data/maps/header_MAP_NATIONAL_PARK_BUG_CATCHING_CONTEST.h"
    ,
    [MAP_NATIONAL_PARK_UNUSED] =
#include "data/maps/header_MAP_NATIONAL_PARK_UNUSED.h"
    ,
    [MAP_ROUTE_10_POWER_PLANT_BROKEN] =
#include "data/maps/header_MAP_ROUTE_10_POWER_PLANT_BROKEN.h"
    ,
    [MAP_RUINS_OF_ALPH_UNDERGROUND_HALL_SINJOH_EVENT] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_UNDERGROUND_HALL_SINJOH_EVENT.h"
    ,
    [MAP_RUINS_OF_ALPH_HALL_ENTRANCE_SINJOH_EVENT] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_HALL_ENTRANCE_SINJOH_EVENT.h"
    ,
    [MAP_RUINS_OF_ALPH_UNDERGROUND_HALL_SINJOH_EVENT_2] =
#include "data/maps/header_MAP_RUINS_OF_ALPH_UNDERGROUND_HALL_SINJOH_EVENT_2.h"
    ,
    [MAP_ROUTE_7_SAFFRON_GATEHOUSE] =
#include "data/maps/header_MAP_ROUTE_7_SAFFRON_GATEHOUSE.h"
    ,
    [MAP_LAVENDER_POKECENTER_B1F] =
#include "data/maps/header_MAP_LAVENDER_POKECENTER_B1F.h"
    ,
    [MAP_CERULEAN_POKECENTER_B1F] =
#include "data/maps/header_MAP_CERULEAN_POKECENTER_B1F.h"
    ,
    [MAP_VIRIDIAN_GYM] =
#include "data/maps/header_MAP_VIRIDIAN_GYM.h"
    ,
    [MAP_VIRIDIAN_NORTHEAST_HOUSE] =
#include "data/maps/header_MAP_VIRIDIAN_NORTHEAST_HOUSE.h"
    ,
    [MAP_VIRIDIAN_TRAINER_HOUSE_1F] =
#include "data/maps/header_MAP_VIRIDIAN_TRAINER_HOUSE_1F.h"
    ,
    [MAP_VIRIDIAN_TRAINER_HOUSE_B1F] =
#include "data/maps/header_MAP_VIRIDIAN_TRAINER_HOUSE_B1F.h"
    ,
    [MAP_VIRIDIAN_POKEMART] =
#include "data/maps/header_MAP_VIRIDIAN_POKEMART.h"
    ,
    [MAP_VIRIDIAN_POKECENTER_1F] =
#include "data/maps/header_MAP_VIRIDIAN_POKECENTER_1F.h"
    ,
    [MAP_VIRIDIAN_POKECENTER_B1F] =
#include "data/maps/header_MAP_VIRIDIAN_POKECENTER_B1F.h"
    ,
    [MAP_PALLET_TOWN_REDS_HOUSE_1F] =
#include "data/maps/header_MAP_PALLET_TOWN_REDS_HOUSE_1F.h"
    ,
    [MAP_PALLET_TOWN_BLUES_HOUSE_1F] =
#include "data/maps/header_MAP_PALLET_TOWN_BLUES_HOUSE_1F.h"
    ,
    [MAP_PALLET_TOWN_OAKS_LAB] =
#include "data/maps/header_MAP_PALLET_TOWN_OAKS_LAB.h"
    ,
    [MAP_PALLET_TOWN_REDS_HOUSE_2F] =
#include "data/maps/header_MAP_PALLET_TOWN_REDS_HOUSE_2F.h"
    ,
    [MAP_PALLET_TOWN_BLUES_HOUSE_2F] =
#include "data/maps/header_MAP_PALLET_TOWN_BLUES_HOUSE_2F.h"
    ,
    [MAP_CINNABAR_ISLAND_POKECENTER_1F] =
#include "data/maps/header_MAP_CINNABAR_ISLAND_POKECENTER_1F.h"
    ,
    [MAP_CINNABAR_ISLAND_POKECENTER_B1F] =
#include "data/maps/header_MAP_CINNABAR_ISLAND_POKECENTER_B1F.h"
    ,
    [MAP_ROUTE_28_HOUSE] =
#include "data/maps/header_MAP_ROUTE_28_HOUSE.h"
    ,
    [MAP_ROUTE_3_POKECENTER_1F] =
#include "data/maps/header_MAP_ROUTE_3_POKECENTER_1F.h"
    ,
    [MAP_ROUTE_3_POKECENTER_B1F] =
#include "data/maps/header_MAP_ROUTE_3_POKECENTER_B1F.h"
    ,
    [MAP_MOUNT_MOON_SQUARE_CLEFAIRY_EVENT] =
#include "data/maps/header_MAP_MOUNT_MOON_SQUARE_CLEFAIRY_EVENT.h"
    ,
    [MAP_MOUNT_SILVER_POKECENTER_1F] =
#include "data/maps/header_MAP_MOUNT_SILVER_POKECENTER_1F.h"
    ,
    [MAP_MOUNT_SILVER_POKECENTER_B1F] =
#include "data/maps/header_MAP_MOUNT_SILVER_POKECENTER_B1F.h"
    ,
    [MAP_WIFI_PLAZA_WARP_ROOM] =
#include "data/maps/header_MAP_WIFI_PLAZA_WARP_ROOM.h"
    ,
    [MAP_ROUTE_5_HOUSE] =
#include "data/maps/header_MAP_ROUTE_5_HOUSE.h"
    ,
    [MAP_MOUNT_MOON_SQUARE_SHOP] =
#include "data/maps/header_MAP_MOUNT_MOON_SQUARE_SHOP.h"
    ,
    [MAP_GOLDENROD_MAGNET_TRAIN_STATION_2F_EMPTY] =
#include "data/maps/header_MAP_GOLDENROD_MAGNET_TRAIN_STATION_2F_EMPTY.h"
    ,
    [MAP_SAFFRON_MAGNET_TRAIN_STATION_2F_EMPTY] =
#include "data/maps/header_MAP_SAFFRON_MAGNET_TRAIN_STATION_2F_EMPTY.h"
    ,
    [MAP_SINJOH_RUINS_EXTERIOR] =
#include "data/maps/header_MAP_SINJOH_RUINS_EXTERIOR.h"
    ,
    [MAP_SINJOH_RUINS_MYSTRI_STAGE] =
#include "data/maps/header_MAP_SINJOH_RUINS_MYSTRI_STAGE.h"
    ,
    [MAP_SINJOH_RUINS_CABIN] =
#include "data/maps/header_MAP_SINJOH_RUINS_CABIN.h"
    ,
    [MAP_EMBEDDED_TOWER_GROUDON_ROOM] =
#include "data/maps/header_MAP_EMBEDDED_TOWER_GROUDON_ROOM.h"
    ,
    [MAP_EMBEDDED_TOWER_KYOGRE_ROOM] =
#include "data/maps/header_MAP_EMBEDDED_TOWER_KYOGRE_ROOM.h"
    ,
    [MAP_EMBEDDED_TOWER_RAYQUAZA_ROOM] =
#include "data/maps/header_MAP_EMBEDDED_TOWER_RAYQUAZA_ROOM.h"
    ,
    [MAP_VIRIDIAN_ROUTE_1_GATEHOUSE] =
#include "data/maps/header_MAP_VIRIDIAN_ROUTE_1_GATEHOUSE.h"
    ,
    [MAP_FRONTIER_ACCESS_POKECENTER_1F] =
#include "data/maps/header_MAP_FRONTIER_ACCESS_POKECENTER_1F.h"
    ,
    [MAP_FRONTIER_ACCESS_POKECENTER_B1F] =
#include "data/maps/header_MAP_FRONTIER_ACCESS_POKECENTER_B1F.h"
    ,
    [MAP_FRONTIER_ACCESS_POKEMART] =
#include "data/maps/header_MAP_FRONTIER_ACCESS_POKEMART.h"
    ,
    [MAP_FRONTIER_ACCESS_MOVE_TUTOR_HOUSE] =
#include "data/maps/header_MAP_FRONTIER_ACCESS_MOVE_TUTOR_HOUSE.h"
    ,
    [MAP_ROUTE_5_UNDERGROUND_PATH] =
#include "data/maps/header_MAP_ROUTE_5_UNDERGROUND_PATH.h"
    ,
    [MAP_ROUTE_12_FISHING_BROTHER_HOUSE] =
#include "data/maps/header_MAP_ROUTE_12_FISHING_BROTHER_HOUSE.h"
    ,
    [MAP_SAFARI_ZONE_GATE_POKECENTER_1F] =
#include "data/maps/header_MAP_SAFARI_ZONE_GATE_POKECENTER_1F.h"
    ,
    [MAP_SAFARI_ZONE_GATE_POKECENTER_B1F] =
#include "data/maps/header_MAP_SAFARI_ZONE_GATE_POKECENTER_B1F.h"
    ,
    [MAP_GOLDENROD_GAME_CORNER] =
#include "data/maps/header_MAP_GOLDENROD_GAME_CORNER.h"
    ,
    [MAP_CELADON_GAME_CORNER] =
#include "data/maps/header_MAP_CELADON_GAME_CORNER.h"
    ,
    [MAP_UNUSED] =
#include "data/maps/header_MAP_UNUSED.h"
    ,
    [MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM] =
#include "data/maps/header_MAP_POKEMON_LEAGUE_ENTRANCE_WIFI_ROOM.h"
    ,
};

#endif
