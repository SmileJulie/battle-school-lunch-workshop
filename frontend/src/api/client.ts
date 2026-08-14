export type School = {
  officeCode: string
  schoolCode: string
  name: string
  officeName: string
  regionName: string
  schoolType: string
}

export type SchoolSearchResponse = {
  schools: School[]
  hasMore: boolean
}

export type Meal = {
  date: string
  mealType: '중식'
  dishes: string[]
  calories?: string | null
  nutrition?: string | null
  origin?: string | null
  servings?: number | null
}

export type MealSearchResponse = {
  school: {
    officeCode: string
    schoolCode: string
  }
  from: string
  to: string
  meals: Meal[]
}

export type ApiError = {
  code: string
  message: string
  requestId: string
}

export class ApiClientError extends Error {
  readonly apiError: ApiError

  constructor(apiError: ApiError) {
    super(apiError.message)
    this.name = 'ApiClientError'
    this.apiError = apiError
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function searchSchools(query: string, signal?: AbortSignal): Promise<SchoolSearchResponse> {
  return request<SchoolSearchResponse>(`/api/schools?query=${encodeURIComponent(query)}`, signal)
}

export async function getMeals(
  school: Pick<School, 'officeCode' | 'schoolCode'>,
  from: string,
  to: string,
  signal?: AbortSignal,
): Promise<MealSearchResponse> {
  const params = new URLSearchParams({
    officeCode: school.officeCode,
    schoolCode: school.schoolCode,
    from,
    to,
  })
  return request<MealSearchResponse>(`/api/meals?${params.toString()}`, signal)
}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { accept: 'application/json' },
    signal,
  })
  const body = await response.json()
  if (!response.ok) {
    const apiError = body?.error as ApiError | undefined
    throw new ApiClientError(
      apiError ?? {
        code: 'UNKNOWN_ERROR',
        message: '요청을 처리하지 못했습니다.',
        requestId: response.headers.get('x-request-id') ?? 'unknown',
      },
    )
  }
  return body as T
}
