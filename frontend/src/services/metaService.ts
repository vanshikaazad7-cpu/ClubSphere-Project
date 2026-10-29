import { api } from './apiClient'
import type { LastUpdatedMetadata } from '../domain/types'

export const metaService = {
  async getLastUpdated(): Promise<LastUpdatedMetadata> {
    return api.get<LastUpdatedMetadata>('/meta/last-updated')
  },
}
