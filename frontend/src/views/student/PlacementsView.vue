<template>
  <div class="container-fluid py-4 px-4">
    <h5 class="fw-bold mb-4">Placement Confirmations</h5>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>
    <div v-else-if="placements.length === 0"
         class="text-muted text-center py-5">
      No placement confirmations yet. Keep applying!
    </div>
    <div v-else class="row g-4">
      <div class="col-md-6" v-for="p in placements" :key="p.id">
        <div class="card border-0 shadow-sm h-100
                    border-start border-4 border-success">
          <div class="card-body">
            <div class="d-flex align-items-start justify-content-between mb-3">
              <div>
                <h5 class="fw-bold mb-1 text-success">Selected!</h5>
                <h6 class="fw-semibold mb-0">{{ p.company_name }}</h6>
              </div>
              <span class="badge bg-success fs-6 fw-normal">Placed</span>
            </div>

            <div class="row g-2 small">
              <div class="col-6">
                <div class="text-muted">Position</div>
                <div class="fw-medium">{{ p.position || '—' }}</div>
              </div>
              <div class="col-6">
                <div class="text-muted">Salary</div>
                <div class="fw-medium">
                  {{ p.salary ? `₹${p.salary} LPA` : '—' }}
                </div>
              </div>
              <div class="col-6">
                <div class="text-muted">Joining Date</div>
                <div class="fw-medium">{{ p.joining_date || 'TBD' }}</div>
              </div>
              <div class="col-6">
                <div class="text-muted">Confirmed on</div>
                <div class="fw-medium">{{ formatDate(p.created_at) }}</div>
              </div>
            </div>
          </div>

          <div class="card-footer bg-transparent">
            <a v-if="p.offer_letter_url"
               :href="p.offer_letter_url"
               target="_blank"
               class="btn btn-success btn-sm w-100">
              Download Offer Letter
            </a>
            <div v-else class="text-muted small text-center py-1">
              Offer letter not uploaded yet
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'StudentPlacementsView',
  data() { return { placements: [], loading: true } },
  async created() {
    try {
      const { data } = await api.get('/student/placements')
      this.placements = data
    } finally { this.loading = false }
  },
  methods: {
    formatDate(d) {
      return d ? new Date(d).toLocaleDateString('en-IN') : '—'
    },
  },
}
</script>
