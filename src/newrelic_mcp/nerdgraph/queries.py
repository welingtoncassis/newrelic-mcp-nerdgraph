"""GraphQL documents used by the services.

Each constant is kept verbatim so it can be pasted into the NerdGraph GraphiQL
explorer (https://api.newrelic.com/graphiql) when debugging a tool.
"""

from __future__ import annotations

NRQL_QUERY = """
query ($accounts: [Int!]!, $nrql: Nrql!, $timeout: Seconds) {
  actor {
    nrql(accounts: $accounts, query: $nrql, timeout: $timeout) {
      results
      metadata {
        eventTypes
        facets
        messages
        timeWindow { begin end }
      }
      totalResult
    }
  }
}
"""

NRQL_QUERY_ASYNC_START = """
query ($accounts: [Int!]!, $nrql: Nrql!) {
  actor {
    nrql(accounts: $accounts, query: $nrql, async: true) {
      queryProgress { queryId completed resultExpiration retryAfter retryDeadline }
      results
    }
  }
}
"""

NRQL_QUERY_ASYNC_POLL = """
query ($accounts: [Int!]!, $queryId: ID!) {
  actor {
    nrqlQueryProgress(accounts: $accounts, queryId: $queryId) {
      queryProgress { queryId completed retryAfter retryDeadline }
      results
    }
  }
}
"""

ENTITY_SEARCH = """
query ($query: String!, $cursor: String) {
  actor {
    entitySearch(query: $query) {
      count
      results(cursor: $cursor) {
        nextCursor
        entities {
          guid
          name
          entityType
          domain
          type
          accountId
          reporting
          tags { key values }
        }
      }
    }
  }
}
"""

ENTITY_DETAILS = """
query ($guid: EntityGuid!) {
  actor {
    entity(guid: $guid) {
      guid
      name
      entityType
      domain
      type
      accountId
      permalink
      reporting
      tags { key values }
      goldenMetrics {
        metrics { name title query unit }
      }
      relationships {
        type
        source { entity { guid name entityType } }
        target { entity { guid name entityType } }
      }
      ... on AlertableEntity {
        alertSeverity
      }
    }
  }
}
"""

ALERT_POLICIES = """
query ($accountId: Int!, $cursor: String) {
  actor {
    account(id: $accountId) {
      alerts {
        policiesSearch(cursor: $cursor) {
          nextCursor
          policies { id name incidentPreference }
        }
      }
    }
  }
}
"""

AI_ISSUES = """
query ($accountId: Int!, $filter: AiIssuesFilterIssues, $cursor: String) {
  actor {
    account(id: $accountId) {
      aiIssues {
        issues(filter: $filter, cursor: $cursor) {
          nextCursor
          issues {
            issueId
            title
            description
            priority
            state
            createdAt
            closedAt
            updatedAt
            entityGuids
            entityNames
            conditionName
            policyName
            totalIncidents
          }
        }
      }
    }
  }
}
"""

NRQL_CONDITIONS = """
query ($accountId: Int!, $policyId: ID, $cursor: String) {
  actor {
    account(id: $accountId) {
      alerts {
        nrqlConditionsSearch(searchCriteria: { policyId: $policyId }, cursor: $cursor) {
          nextCursor
          nrqlConditions {
            id
            name
            enabled
            policyId
            type
            nrql { query }
            terms { operator priority threshold thresholdDuration thresholdOccurrences }
          }
        }
      }
    }
  }
}
"""
