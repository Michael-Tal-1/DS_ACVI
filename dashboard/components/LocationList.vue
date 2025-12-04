<template>
  <div class="card sticky-top top-2">
    <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
      <span>Locations Ranking</span>
      <small>{{ locations.length }} total</small>
    </div>
    <div class="card-body p-0" style="padding: 0 !important;">
      <div class="table-responsive location-list">
        <table class="table table-hover mb-0">
          <thead class="table-light sticky-top">
            <tr>
              <th>#</th>
              <th>Location</th>
              <th class="text-end sortable" @click="$emit('toggle-sort')">
                ACVI
                <span v-if="sortAscending">▲</span>
                <span v-else>▼</span>
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(loc, index) in locations"
                :key="loc.name"
                @click="$emit('select-location', loc)"
                :class="{'table-active': selectedLocations.includes(loc.name), 'location-row': true}">
              <td>{{ index + 1 }}</td>
              <td>
                <span v-if="compareMode && selectedLocations.includes(loc.name)" class="badge bg-primary me-1">
                  {{ selectedLocations.indexOf(loc.name) + 1 }}
                </span>
                {{ loc.name }}
              </td>
              <td class="text-end">
                <span class="badge" :class="getScoreBadge(loc.data.acvi_score)">
                  {{ loc.data.acvi_score.toFixed(2) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    locations: {
      type: Array,
      required: true
    },
    selectedLocations: {
      type: Array,
      required: true
    },
    compareMode: {
      type: Boolean,
      required: true
    },
    sortAscending: {
      type: Boolean,
      required: true
    }
  },
  methods: {
    getScoreBadge(score) {
      if (score >= 70) return 'bg-danger'
      if (score >= 50) return 'bg-warning'
      return 'bg-success'
    }
  }
}
</script>

<style>

.top-2 {
  top: 0.5rem;
}

</style>