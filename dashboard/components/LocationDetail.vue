<template>
  <div class="card">
    <div class="card-header bg-primary">
      <h5 class="mb-0 text-white">{{ locationName }}</h5>
    </div>
    <div class="card-body">
      <div class="row mb-3">
        <div class="col-md-12">
          <div class="text-center mb-3">
            <h2 class="mb-1">ACVI Score</h2>
            <div class="display-3 fw-bold" :class="getScoreColor(locationData.acvi_score)">
              {{ locationData.acvi_score.toFixed(2) }}
            </div>
            <small class="text-muted formula-hover" title="ACVI = (w₁ × TV) + (w₂ × PV) + (w₃ × MS) + (w₄ × EE)">
              Hover for formula
            </small>
          </div>
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-md-12">
          <h6 class="border-bottom pb-2">Component Breakdown</h6>
          <div class="row g-2">
            <div v-for="(value, component) in locationData.components" :key="component" class="col-md-6">
              <div class="component-card" :title="getFormula(component)">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <span class="component-name">{{ formatName(component) }}</span>
                  <span class="badge bg-secondary">{{ (locationData.weights[component] * 100).toFixed(0) }}%</span>
                </div>
                <div class="progress mb-1" style="height: 20px;">
                  <div class="progress-bar" :class="getBarClass(value)"
                       :style="{width: value + '%'}">
                    {{ value.toFixed(1) }}
                  </div>
                </div>
                <div class="d-flex justify-content-between small text-muted">
                  <span>Raw: {{ locationData.components_raw[component].toFixed(2) }}</span>
                  <span>Normalized: {{ value.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-md-12">
          <h6 class="border-bottom pb-2">ACVI Calculation Example</h6>
          <div class="calculation-example">
            <div class="formula-box">
              <strong>Formula:</strong><br>
              ACVI = (w₁ × TV) + (w₂ × PV) + (w₃ × MS) + (w₄ × EE)
            </div>
            <div class="calculation-steps mt-2">
              <div v-for="(value, component) in locationData.components" :key="component" class="calc-step">
                {{ (locationData.weights[component] * 100).toFixed(0) }}% × {{ value.toFixed(2) }} =
                <strong>{{ (locationData.weights[component] * value).toFixed(3) }}</strong>
              </div>
              <div class="calc-step border-top pt-2 mt-2 fw-bold">
                Total ACVI = {{ locationData.acvi_score.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col-md-12">
          <ClimateChart :location-name="locationName" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    locationName: {
      type: String,
      required: true
    },
    locationData: {
      type: Object,
      required: true
    }
  },
  methods: {
    getScoreColor(score) {
      if (score >= 70) return 'text-danger'
      if (score >= 50) return 'text-warning'
      return 'text-success'
    },
    formatName(name) {
      return name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')
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
    }
  }
}
</script>
