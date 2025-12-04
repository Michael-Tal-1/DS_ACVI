<template>
  <div id="app">
    <nav class="navbar">
      <div class="container-fluid px-4">
        <span class="navbar-brand mb-0">ACVI Dashboard</span>
        <div class="d-flex align-items-center gap-2">
          <span class="me-2" style="color: #850906; font-weight: 500;">{{ Object.keys(locations).length }} Locations</span>
          <button
            class="btn btn-sm"
            :class="mapView ? 'btn-primary' : 'btn-outline-primary'"
            @click="toggleMap">
            {{ mapView ? 'List View' : 'Map View' }}
          </button>
          <button
            class="btn btn-sm btn-primary"
            @click="toggleCompare"
            v-if="!mapView">
            {{ compareMode ? 'Exit Compare' : 'Compare Mode' }}
          </button>
        </div>
      </div>
    </nav>

    <div class="container-fluid mt-4 px-4">
      <div class="row" v-if="!mapView">
        <div class="col-md-4">
          <LocationList
            :locations="sortedLocations"
            :selected-locations="selectedLocations"
            :compare-mode="compareMode"
            :sort-ascending="sortAscending"
            @select-location="selectLocation"
            @toggle-sort="toggleSort"
          />
        </div>

        <div class="col-md-8">
          <LocationDetail
            v-if="!compareMode && selectedLocations.length === 1"
            :location-name="selectedLocations[0]"
            :location-data="locations[selectedLocations[0]]"
          />

          <CompareView
            v-else-if="compareMode && selectedLocations.length > 0"
            :location-names="selectedLocations"
            :locations="locations"
          />

          <div v-else class="card">
            <div class="card-header bg-primary">
              <h5 class="mb-0 text-white">{{ compareMode ? 'Comparison' : 'Location Details' }}</h5>
            </div>
            <div class="card-body text-center text-muted py-5">
              <h4>{{ compareMode ? 'Select locations to compare' : 'Select a location to view details' }}</h4>
              <p v-if="compareMode">Click on locations from the list (max 4)</p>
            </div>
          </div>
        </div>
      </div>

      <div class="row" v-if="mapView">
        <div class="col-md-12">
          <MapView
            :locations="locations"
            @location-selected="handleMapLocationSelect"
          />
        </div>
      </div>
    </div>

    <footer class="footer mt-4">
      <div class="container-fluid px-4 py-4">
        <div class="row mb-3">
          <div class="col-md-12">
            <div class="d-flex align-items-center mb-3">
              <svg width="24" height="24" viewBox="0 0 16 16" fill="#850906" class="me-2">
                <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
              </svg>
              <a href="https://github.com/Michael-Tal-1/DS_ACVI" target="_blank" class="footer-project-link">
                View Project on GitHub
              </a>
            </div>
            <p class="mb-2 footer-text">
              Created as part of <strong>Data Science Methodology</strong> by students of <strong>National Technical University of Ukraine "Igor Sikorsky Kyiv Polytechnic Institute"</strong>
            </p>
          </div>
        </div>

        <div class="row">
          <div class="mb-3 mb-md-0">
            <h6 class="footer-heading">Team Members</h6>
            <div class="row">
              <div class="team-member col-4">
                <div class="member-name">Tal Michael</div>
                <div class="member-links">
                  <a href="https://github.com/Michael-Tal-1" target="_blank" class="icon-link" title="GitHub">
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                  </a>
                  <a href="https://michaeltal.dev" target="_blank" class="icon-link" title="Website">
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm7.5-6.923c-.67.204-1.335.82-1.887 1.855A7.97 7.97 0 0 0 5.145 4H7.5V1.077zM4.09 4a9.267 9.267 0 0 1 .64-1.539 6.7 6.7 0 0 1 .597-.933A7.025 7.025 0 0 0 2.255 4H4.09zm-.582 3.5c.03-.877.138-1.718.312-2.5H1.674a6.958 6.958 0 0 0-.656 2.5h2.49zM4.847 5a12.5 12.5 0 0 0-.338 2.5H7.5V5H4.847zM8.5 5v2.5h2.99a12.495 12.495 0 0 0-.337-2.5H8.5zM4.51 8.5a12.5 12.5 0 0 0 .337 2.5H7.5V8.5H4.51zm3.99 0V11h2.653c.187-.765.306-1.608.338-2.5H8.5zM5.145 12c.138.386.295.744.468 1.068.552 1.035 1.218 1.65 1.887 1.855V12H5.145zm.182 2.472a6.696 6.696 0 0 1-.597-.933A9.268 9.268 0 0 1 4.09 12H2.255a7.024 7.024 0 0 0 3.072 2.472zM3.82 11a13.652 13.652 0 0 1-.312-2.5h-2.49c.062.89.291 1.733.656 2.5H3.82zm6.853 3.472A7.024 7.024 0 0 0 13.745 12H11.91a9.27 9.27 0 0 1-.64 1.539 6.688 6.688 0 0 1-.597.933zM8.5 12v2.923c.67-.204 1.335-.82 1.887-1.855.173-.324.33-.682.468-1.068H8.5zm3.68-1h2.146c.365-.767.594-1.61.656-2.5h-2.49a13.65 13.65 0 0 1-.312 2.5zm2.802-3.5a6.959 6.959 0 0 0-.656-2.5H12.18c.174.782.282 1.623.312 2.5h2.49zM11.27 2.461c.247.464.462.98.64 1.539h1.835a7.024 7.024 0 0 0-3.072-2.472c.218.284.418.598.597.933zM10.855 4a7.966 7.966 0 0 0-.468-1.068C9.835 1.897 9.17 1.282 8.5 1.077V4h2.355z"/>
                    </svg>
                  </a>
                </div>
              </div>

              <div class="team-member col-4">
                <div class="member-name">Dmytrenko Vladislav</div>
                <div class="member-links">
                  <a href="https://github.com/posulka50" target="_blank" class="icon-link" title="GitHub">
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                  </a>
                </div>
              </div>

              <div class="team-member col-4">
                <div class="member-name">Piddubna Maria</div>
                <div class="member-links">
                  <a href="https://github.com/piddubnamariia" target="_blank" class="icon-link" title="GitHub">
                    <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                    </svg>
                  </a>
                </div>
              </div>
            </div>
          </div>

          <div class="col-12">
              <div>
                <h6 class="footer-heading">Support Ukraine</h6>
                <a href="https://savelife.in.ua/" target="_blank" class="support-link">
                  Come Back Alive  <span class="ukraine-flag">🇺🇦</span>
                </a>
              </div>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      locations: {},
      selectedLocations: [],
      compareMode: false,
      sortAscending: false,
      mapView: false
    }
  },
  computed: {
    sortedLocations() {
      const locArray = Object.keys(this.locations).map(name => ({
        name,
        data: this.locations[name]
      }))

      return locArray.sort((a, b) => {
        const scoreA = a.data.acvi_score
        const scoreB = b.data.acvi_score
        return this.sortAscending ? scoreA - scoreB : scoreB - scoreA
      })
    }
  },
  methods: {
    selectLocation(location) {
      if (this.compareMode) {
        const index = this.selectedLocations.indexOf(location.name)
        if (index > -1) {
          this.selectedLocations.splice(index, 1)
        } else if (this.selectedLocations.length < 4) {
          this.selectedLocations.push(location.name)
        }
      } else {
        this.selectedLocations = [location.name]
      }
    },
    toggleCompare() {
      this.compareMode = !this.compareMode
      if (!this.compareMode && this.selectedLocations.length > 1) {
        this.selectedLocations = [this.selectedLocations[0]]
      }
    },
    toggleSort() {
      this.sortAscending = !this.sortAscending
    },
    toggleMap() {
      this.mapView = !this.mapView
      if (this.mapView) {
        this.compareMode = false
      }
    },
    handleMapLocationSelect(locationName) {
      this.mapView = false
      this.selectedLocations = [locationName]
    }
  },
  async mounted() {
    try {
      console.log('Fetching data...')
      const response = await fetch('/data/acvi_scores.json')
      console.log('Response status:', response.status)
      this.locations = await response.json()
      console.log('Locations loaded:', Object.keys(this.locations).length)
    } catch (error) {
      console.error('Error loading data:', error)
    }
  }
}
</script>

<style>
.main-info {
  padding: 4rem;
}
</style>