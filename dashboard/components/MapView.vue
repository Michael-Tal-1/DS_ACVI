<template>
  <div class="card">
    <div class="card-header bg-primary">
      <div class="d-flex justify-content-between align-items-center">
        <h5 class="mb-0 text-white">ACVI Global Map</h5>
        <small class="text-white" style="opacity: 0.9;">Showing UN-recognized borders</small>
      </div>
    </div>
    <div class="card-body p-0">
      <div class="map-legend">
        <div class="legend-title">ACVI Score</div>
        <div class="legend-item">
          <span class="legend-color" style="background: #28a745;"></span>
          <span class="legend-text">Low (0-50)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #ffc107;"></span>
          <span class="legend-text">Medium (50-70)</span>
        </div>
        <div class="legend-item">
          <span class="legend-color" style="background: #dc3545;"></span>
          <span class="legend-text">High (70+)</span>
        </div>
      </div>
      <div id="map" ref="map"></div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    locations: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      map: null,
      markers: [],
      coordinates: {
        UA_Center_Kirovohrad: { lat: 48.50, lon: 32.26 },
        UA_South_Kherson: { lat: 46.63, lon: 32.61 },
        UA_West_Ternopil: { lat: 49.55, lon: 25.59 },
        UA_North_Chernihiv: { lat: 51.49, lon: 31.28 },
        UA_East_Kharkiv: { lat: 49.99, lon: 36.23 },
        UA_Vinnytsia: { lat: 49.23, lon: 28.46 },
        UA_Poltava: { lat: 49.58, lon: 34.55 },
        UA_Odesa: { lat: 46.48, lon: 30.72 },
        UA_Zhytomyr: { lat: 50.25, lon: 28.66 },
        UA_Lviv: { lat: 49.83, lon: 24.02 },
        PL_Mazowieckie: { lat: 52.22, lon: 21.01 },
        PL_Wielkopolskie: { lat: 52.40, lon: 16.92 },
        DE_Bavaria: { lat: 48.79, lon: 11.61 },
        DE_LowerSaxony: { lat: 52.63, lon: 9.84 },
        FR_Beauce: { lat: 48.44, lon: 1.51 },
        FR_Bordeaux: { lat: 44.83, lon: -0.57 },
        RO_Wallachia: { lat: 44.42, lon: 26.10 },
        RO_Moldavia: { lat: 46.56, lon: 26.91 },
        HU_Puszta: { lat: 47.16, lon: 19.50 },
        IT_PoValley: { lat: 45.07, lon: 7.68 },
        ES_Andalusia: { lat: 37.38, lon: -5.98 },
        ES_CastillaLeon: { lat: 41.65, lon: -4.72 },
        NL_Flevoland: { lat: 52.52, lon: 5.47 },
        UK_Lincolnshire: { lat: 53.23, lon: -0.54 },
        US_Iowa: { lat: 41.87, lon: -93.60 },
        US_Kansas: { lat: 39.01, lon: -98.48 },
        US_Illinois: { lat: 40.63, lon: -89.39 },
        US_Nebraska: { lat: 41.49, lon: -99.90 },
        US_California_CentralValley: { lat: 36.77, lon: -119.41 },
        US_NorthDakota: { lat: 47.55, lon: -101.00 },
        US_Minnesota: { lat: 46.72, lon: -94.68 },
        CA_Saskatchewan: { lat: 52.93, lon: -106.45 },
        CA_Alberta: { lat: 53.93, lon: -116.57 },
        CA_Manitoba: { lat: 49.89, lon: -97.13 },
        BR_MatoGrosso: { lat: -12.68, lon: -56.92 },
        BR_Parana: { lat: -25.25, lon: -52.02 },
        BR_Goias: { lat: -15.82, lon: -49.84 },
        AR_BuenosAires: { lat: -38.41, lon: -63.61 },
        AR_Cordoba: { lat: -31.42, lon: -64.18 },
        AR_SantaFe: { lat: -31.61, lon: -60.69 },
        AR_LaPampa: { lat: -36.61, lon: -64.28 },
        CN_Henan: { lat: 33.88, lon: 113.61 },
        CN_Heilongjiang: { lat: 45.75, lon: 126.63 },
        CN_Shandong: { lat: 36.65, lon: 117.12 },
        CN_Jilin: { lat: 43.81, lon: 126.55 },
        IN_Punjab: { lat: 30.73, lon: 76.77 },
        IN_MadhyaPradesh: { lat: 23.47, lon: 77.94 },
        IN_UttarPradesh: { lat: 26.84, lon: 80.94 },
        KZ_Kostanay: { lat: 53.21, lon: 63.63 },
        KZ_Akmola: { lat: 51.16, lon: 71.47 },
        TR_Konya: { lat: 37.87, lon: 32.48 },
        ZA_FreeState: { lat: -29.08, lon: 26.15 },
        ZA_WesternCape: { lat: -33.92, lon: 18.42 },
        AU_NewSouthWales: { lat: -31.84, lon: 145.61 },
        AU_WesternAustralia: { lat: -31.95, lon: 115.86 },
        AU_Victoria: { lat: -37.02, lon: 144.96 },
        EG_NileDelta: { lat: 30.04, lon: 31.23 }
      }
    }
  },
  methods: {
    getMarkerColor(score) {
      if (score >= 70) return '#dc3545'
      if (score >= 50) return '#ffc107'
      return '#28a745'
    },
    async initMap() {
      if (!process.client) return

      const L = (await import('leaflet')).default

      await import('leaflet/dist/leaflet.css')

      this.map = L.map(this.$refs.map).setView([30, 0], 2)

      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '© OpenStreetMap contributors, © CARTO | Borders: UN recognized',
        maxZoom: 19,
        subdomains: 'abcd'
      }).addTo(this.map)

      Object.keys(this.locations).forEach(locationName => {
        const coords = this.coordinates[locationName]
        if (!coords) return

        const data = this.locations[locationName]
        const score = data.acvi_score
        const color = this.getMarkerColor(score)

        const marker = L.circleMarker([coords.lat, coords.lon], {
          radius: 8,
          fillColor: color,
          color: '#fff',
          weight: 2,
          opacity: 1,
          fillOpacity: 0.8
        }).addTo(this.map)

        const popupContent = `
          <div class="map-popup">
            <strong>${locationName}</strong><br>
            <span style="color: ${color}; font-weight: 600;">ACVI: ${score.toFixed(2)}</span><br>
            <small>Click marker for details</small>
          </div>
        `

        marker.bindPopup(popupContent)

        marker.on('click', () => {
          this.$emit('location-selected', locationName)
        })

        this.markers.push(marker)
      })
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initMap()
    })
  },
  beforeUnmount() {
    if (this.map) {
      this.map.remove()
    }
  }
}
</script>

<style scoped>
#map {
  height: 600px;
  width: 100%;
}

.map-legend {
  position: absolute;
  top: 70px;
  right: 10px;
  background: white;
  padding: 12px 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-family: 'Manrope', sans-serif;
}

.legend-title {
  font-weight: 700;
  font-size: 0.9rem;
  color: #850906;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.legend-item {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.legend-item:last-child {
  margin-bottom: 0;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  margin-right: 8px;
  border: 2px solid white;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
}

.legend-text {
  font-size: 0.85rem;
  color: #333;
  font-weight: 500;
}
</style>

<style>
.map-popup {
  text-align: center;
  font-family: 'Manrope', sans-serif;
}

.map-popup strong {
  font-size: 1rem;
  color: #333;
}
</style>
