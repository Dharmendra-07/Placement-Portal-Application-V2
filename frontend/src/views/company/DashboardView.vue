<template>
  <div class="container-fluid py-4 px-4">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Header -->
      <div class="d-flex align-items-start justify-content-between mb-4 flex-wrap gap-2">
        <div>
          <h5 class="fw-bold mb-0">{{ data.company?.name }}</h5>
          <span class="text-muted small">{{ data.company?.industry }} · {{ data.company?.location }}</span>
        </div>
        <router-link to="/company/drives" class="btn btn-primary btn-sm">
          + Create Drive
        </router-link>
      </div>

      <!-- Stat cards -->
      <div class="row g-3 mb-4">
        <div class="col-6 col-md-4 col-lg-2" v-for="s in statCards" :key="s.label">
          <div class="card border-0 shadow-sm text-center h-100">
            <div class="card-body py-3">
              <div class="fs-2 fw-bold" :class="s.color">{{ s.value }}</div>
              <div class="text-muted small mt-1">{{ s.label }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Active drives + recent applications side by side -->
      <div class="row g-4">
        <!-- Active drives -->
        <div class="col-lg-7">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold d-flex justify-content-between align-items-center">
              Active Drives
              <router-link to="/company/drives" class="btn btn-sm btn-outline-primary">
                Manage all
              </router-link>
            </div>
            <div class="card-body p-0">
              <div v-if="!data.active_drives?.length"
                   class="text-muted text-center py-4 small">
                No active drives. Create one to start recruiting.
              </div>
              <div v-else class="list-group list-group-flush">
                <div v-for="d in data.active_drives" :key="d.id"
                     class="list-group-item py-3">
                  <div class="d-flex justify-content-between align-items-start">
                    <div>
                      <div class="fw-medium">{{ d.job_title }}</div>
                      <div class="text-muted small">
                        {{ d.job_type }} · {{ d.location || 'Remote' }} ·
                        Deadline: {{ formatDate(d.application_deadline) }}
                      </div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                      <span class="badge bg-secondary">{{ d.applicant_count }} applied</span>
                      <router-link :to="`/company/applicants/${d.id}`"
                                   class="btn btn-sm btn-outline-primary">
                        Review
                      </router-link>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recent applications -->
        <div class="col-lg-5">
          <div class="card border-0 shadow-sm h-100">
            <div class="card-header bg-white fw-semibold">Recent Applications</div>
            <div class="card-body p-0">
              <div v-if="!data.recent_applications?.length"
                   class="text-muted text-center py-4 small">
                No applications yet.
              </div>
              <ul v-else class="list-group list-group-flush">
                <li v-for="a in data.recent_applications" :key="a.id"
                    class="list-group-item py-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <div>
                      <div class="fw-medium small">{{ a.student_name }}</div>
                      <div class="text-muted" style="font-size:11px">
                        {{ a.job_title }} · {{ a.student_dept }}
                      </div>
                    </div>
                    <span class="badge" :class="appBadge(a.status)">{{ a.status }}</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Pending drives -->
      <div v-if="data.pending_drives?.length" class="card border-0 shadow-sm mt-4">
        <div class="card-header bg-white fw-semibold d-flex align-items-center gap-2">
          Drives Awaiting Approval
          <span class="badge bg-warning text-dark">{{ data.pending_drives.length }}</span>
        </div>
        <div class="card-body p-0">
          <ul class="list-group list-group-flush">
            <li v-for="d in data.pending_drives" :key="d.id"
                class="list-group-item d-flex justify-content-between align-items-center py-2">
              <div>
                <span class="fw-medium small">{{ d.job_title }}</span>
                <span class="text-muted small ms-2">submitted {{ formatDate(d.created_at) }}</span>
              </div>
              <span class="badge bg-warning text-dark">Pending</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../../api'

export default {
  name: 'CompanyDashboard',
  data() { return { loading: true, data: {} } },
  computed: {
    statCards() {
      const s = this.data.stats || {}
      return [
        { label: 'Active drives',   value: s.active_drives      || 0, color: 'text-success'  },
        { label: 'Pending approval',value: s.pending_drives      || 0, color: 'text-warning'  },
        { label: 'Closed drives',   value: s.closed_drives       || 0, color: 'text-secondary'},
        { label: 'Total applicants',value: s.total_applications  || 0, color: 'text-primary'  },
        { label: 'Shortlisted',     value: s.shortlisted         || 0, color: 'text-info'     },
        { label: 'Selected',        value: s.selected            || 0, color: 'text-success'  },
      ]
    },
  },
  async created() {
    try {
      const { data } = await api.get('/company/dashboard')
      this.data = data
    } finally { this.loading = false }
  },
  methods: {
    appBadge(s) {
      return {
        applied: 'bg-secondary', shortlisted: 'bg-info text-dark',
        selected: 'bg-success',  rejected: 'bg-danger',
        waiting:  'bg-warning text-dark',
      }[s] || 'bg-secondary'
    },
    formatDate(d) { return d ? new Date(d).toLocaleDateString('en-IN') : '—' },
  },
}
</script>
