<template>
  <div class="card">
    <div class="card-header bg-primary">
      <h5 class="mb-0 text-white">Location Comparison</h5>
    </div>
    <div class="card-body">
      <div v-if="locationNames.length < 2" class="alert alert-info">
        Select at least 2 locations to compare
      </div>

      <div v-else>
        <div class="table-responsive mb-3">
          <table class="table table-bordered table-sm">
            <thead class="table-light">
              <tr>
                <th>Metric</th>
                <th v-for="name in locationNames" :key="name" class="text-center">
                  {{ name }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="fw-bold">ACVI Score</td>
                <td v-for="name in locationNames" :key="name" class="text-center">
                  <span class="badge" :class="getScoreBadge(locations[name].acvi_score)">
                    {{ locations[name].acvi_score.toFixed(2) }}
                  </span>
                </td>
              </tr>
              <tr v-for="component in componentList" :key="component">
                <td>
                  <span class="formula-hover" :title="getFormula(component)">
                    {{ formatName(component) }}
                  </span>
                  <small class="text-muted d-block">
                    Weight: {{ (locations[locationNames[0]].weights[component] * 100).toFixed(0) }}%
                  </small>
                </td>
                <td v-for="name in locationNames" :key="name" class="text-center">
                  <div class="mb-1">
                    <div class="progress" style="height: 20px;">
                      <div class="progress-bar"
                           :class="getBarClass(locations[name].components[component])"
                           :style="{width: locations[name].components[component] + '%'}">
                        {{ locations[name].components[component].toFixed(1) }}
                      </div>
                    </div>
                  </div>
                  <small class="text-muted">
                    Raw: {{ locations[name].components_raw[component].toFixed(2) }}
                  </small>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="row">
          <div class="col-md-12">
            <h6 class="border-bottom pb-2">Component Comparison Chart</h6>
            <canvas ref="compareChart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    locationNames: {
      type: Array,
      required: true
    },
    locations: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      componentList: ['temperature_volatility', 'precipitation_volatility', 'moisture_stress', 'extreme_events'],
      chart: null
    }
  },
  methods: {
    formatName(name) {
      return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
    },
    getScoreBadge(score) {
      if (score >= 70) return 'bg-danger'
      if (score >= 50) return 'bg-warning'
      return 'bg-success'
    },
    getBarClass(value) {
      if (value >= 70) return 'bg-danger'
      if (value >= 50) return 'bg-warning'
      return 'bg-success'
    },
    getFormula(component) {
      const formulas = {
        temperature_volatility: 'TV = mean(CV_T2M_RANGE, CV_T2M, HeatStressDays%, CV_GDD)',
        precipitation_volatility: 'PV = mean(CV_PRECTOTCORR, CV_YearlyTotal, MaxDrySpell)',
        moisture_stress: 'MS = mean((1-GWETROOT)×100, CV_GWETROOT, VPD/2.5×100, CV_EVPTRNS)',
        extreme_events: 'EE = mean(HeatDays/30×100, FrostDays/20×100, DryDays/90×100, ExtremeWind%, CV_RADIATION)'
      }
      return formulas[component] || ''
    },
    async createChart() {
      if (this.locationNames.length < 2) return
      if (!process.client) return

      await this.$nextTick()

      const canvas = this.$refs.compareChart
      if (!canvas) return

      const Chart = (await import('chart.js/auto')).default

      if (this.chart) {
        this.chart.destroy()
      }

      const colors = [
        'rgb(255, 99, 132)',
        'rgb(54, 162, 235)',
        'rgb(255, 206, 86)',
        'rgb(75, 192, 192)'
      ]

      const datasets = this.locationNames.map((name, index) => {
        return {
          label: name,
          data: this.componentList.map(comp => this.locations[name].components[comp]),
          borderColor: colors[index],
          backgroundColor: colors[index].replace('rgb', 'rgba').replace(')', ', 0.2)'),
          pointBackgroundColor: colors[index],
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: colors[index]
        }
      })

      this.chart = new Chart(canvas, {
        type: 'radar',
        data: {
          labels: this.componentList.map(this.formatName),
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          aspectRatio: 2,
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
              ticks: {
                stepSize: 20
              }
            }
          }
        }
      })
    }
  },
  watch: {
    locationNames: {
      handler() {
        this.createChart()
      },
      deep: true
    }
  },
  mounted() {
    this.createChart()
  }
}
</script>
