<template>
  <div>
    <h6 class="border-bottom pb-2">Raw Climate Data</h6>
    <div class="btn-group btn-group-sm mb-2" role="group">
      <button v-for="param in climateParams" :key="param"
              @click="selectedParam = param"
              class="btn"
              :class="selectedParam === param ? 'btn-primary' : 'btn-outline-primary'">
        {{ param }}
      </button>
    </div>
    <div class="raw-data-container">
      <canvas ref="climateChart"></canvas>
    </div>
    <div class="mt-2">
      <small class="text-muted">
        <strong>{{ selectedParam }}:</strong> {{ getParamDesc(selectedParam) }}
      </small>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    locationName: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      selectedParam: 'T2M',
      climateParams: ['T2M', 'PRECTOTCORR', 'GWETROOT', 'RH2M', 'WS10M_MAX', 'EVPTRNS'],
      chart: null
    }
  },
  methods: {
    getParamDesc(param) {
      const descriptions = {
        'T2M': 'Temperature at 2 Meters (°C)',
        'PRECTOTCORR': 'Precipitation Corrected (mm/day)',
        'GWETROOT': 'Root Zone Soil Wetness (0-1)',
        'RH2M': 'Relative Humidity at 2 Meters (%)',
        'WS10M_MAX': 'Maximum Wind Speed at 10 Meters (m/s)',
        'EVPTRNS': 'Evapotranspiration (mm/day)'
      }
      return descriptions[param] || param
    },
    generateSampleData(param) {
      const labels = []
      const values = []

      for (let year = 2009; year <= 2023; year++) {
        for (let month = 1; month <= 12; month++) {
          labels.push(`${year}-${String(month).padStart(2, '0')}`)

          let baseValue, variance
          switch(param) {
            case 'T2M':
              baseValue = 15 + 10 * Math.sin((month - 1) / 12 * Math.PI * 2)
              variance = 5
              break
            case 'PRECTOTCORR':
              baseValue = 2 + Math.random() * 3
              variance = 2
              break
            case 'GWETROOT':
              baseValue = 0.5 + 0.2 * Math.sin((month - 1) / 12 * Math.PI * 2)
              variance = 0.1
              break
            case 'RH2M':
              baseValue = 65 + 15 * Math.sin((month - 1) / 12 * Math.PI * 2)
              variance = 10
              break
            case 'WS10M_MAX':
              baseValue = 8 + 2 * Math.random()
              variance = 3
              break
            case 'EVPTRNS':
              baseValue = 3 + 2 * Math.sin((month - 1) / 12 * Math.PI * 2)
              variance = 1
              break
            default:
              baseValue = 50
              variance = 10
          }

          values.push(baseValue + (Math.random() - 0.5) * variance)
        }
      }

      return {
        labels: labels.filter((_, i) => i % 3 === 0),
        values: values.filter((_, i) => i % 3 === 0)
      }
    },
    async createChart() {
      if (!process.client) return

      await this.$nextTick()

      const canvas = this.$refs.climateChart
      if (!canvas) return

      const Chart = (await import('chart.js/auto')).default

      if (this.chart) {
        this.chart.destroy()
      }

      const sampleData = this.generateSampleData(this.selectedParam)

      this.chart = new Chart(canvas, {
        type: 'line',
        data: {
          labels: sampleData.labels,
          datasets: [{
            label: this.selectedParam,
            data: sampleData.values,
            borderColor: 'rgb(75, 192, 192)',
            backgroundColor: 'rgba(75, 192, 192, 0.1)',
            tension: 0.1,
            pointRadius: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 3,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: false,
              title: {
                display: true,
                text: this.getParamDesc(this.selectedParam)
              }
            },
            x: {
              title: {
                display: true,
                text: 'Time (Monthly Aggregates)'
              }
            }
          }
        }
      })
    }
  },
  watch: {
    selectedParam() {
      this.createChart()
    }
  },
  mounted() {
    this.createChart()
  }
}
</script>
