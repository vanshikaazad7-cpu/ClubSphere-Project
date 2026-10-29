import { api } from './apiClient'
import type { Paginated, Proposal } from '../domain/types'

export interface CreateProposalInput {
  proposed_name: string
  program_id: number
  description: string
}

export type ReviewDecision = 'approve' | 'reject' | 'changes_requested'

export interface ReviewProposalInput {
  decision: ReviewDecision
  comment?: string | null
}

export const proposalService = {
  async getProposals(params: { status?: string; page?: number; page_size?: number } = {}): Promise<Paginated<Proposal>> {
    const query = new URLSearchParams()
    query.set('page', String(params.page ?? 1))
    query.set('page_size', String(params.page_size ?? 50))
    if (params.status) query.set('status', params.status)

    return api.get<Paginated<Proposal>>(`/proposals?${query.toString()}`)
  },

  async createProposal(input: CreateProposalInput): Promise<Proposal> {
    return api.post<Proposal>('/proposals', input)
  },

  async reviewProposal(proposalId: number, input: ReviewProposalInput): Promise<Proposal> {
    return api.post<Proposal>(`/proposals/${proposalId}/review`, input)
  },
}
