from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FullDepthProviderStatus:
    provider_name: str
    implemented_flag: int
    source_status: str
    reason: str


class FullDepthBookProviderUnavailable(RuntimeError):
    pass


class FullDepthBookArchive:
    """Provider contract for future full-depth stock order book capture.

    Alpaca stock market-data streams expose NBBO quotes, not full exchange depth.
    This class deliberately fails fast until a direct-depth provider is wired in,
    such as Nasdaq TotalView/ITCH or another licensed depth feed.
    """

    def __init__(self, *, output_dir: Path, provider_name: str = "UNCONFIGURED_FULL_DEPTH_PROVIDER") -> None:
        self.output_dir = output_dir
        self.provider_name = provider_name

    def readiness(self) -> FullDepthProviderStatus:
        return FullDepthProviderStatus(
            provider_name=self.provider_name,
            implemented_flag=0,
            source_status="provider_required_not_available_from_alpaca_stock_api",
            reason="Alpaca stock quotes provide NBBO bid/ask and size, not full depth book levels.",
        )

    def run(self) -> None:
        status = self.readiness()
        raise FullDepthBookProviderUnavailable(status.reason)
