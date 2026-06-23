export type ReadModelAuthority = "NOT_AUTHORITY";

export type ReadModelBoundary = {
  authority: ReadModelAuthority;
  source: "static_fixture_snapshot";
  runtimeConnectionPermitted: false;
  directDbAccessPermitted: false;
  brokerMutationPermitted: false;
};

export const scaffoldReadModelBoundary: ReadModelBoundary = {
  authority: "NOT_AUTHORITY",
  source: "static_fixture_snapshot",
  runtimeConnectionPermitted: false,
  directDbAccessPermitted: false,
  brokerMutationPermitted: false,
};

export function assertScaffoldReadModelBoundary(boundary: ReadModelBoundary): ReadModelBoundary {
  return boundary;
}
