from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from researcher.config import RepositoryConfig
from researcher.models import DocumentSearchResult, SearchResult
from researcher.services.model_archive_service import PackResult


def present_index_results(repo_results: list[dict], console: Console) -> None:
    for serialized in repo_results:
        console.print(
            f"[green]✓[/green] [bold]{serialized['repository']}[/bold]: {serialized['documents_indexed']} indexed, "
            f"{serialized['documents_skipped']} skipped, {serialized['documents_failed']} failed, "
            f"{serialized['documents_purged']} purged, {serialized['fragments_created']} fragments"
        )
        for error in serialized["errors"]:
            console.print(f"  [red]✗[/red] {error}")


def present_status(repo_stats: list[dict], console: Console) -> None:
    for stat in repo_stats:
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="bold")
        table.add_column("Value")
        table.add_row("Repository", stat["repository_name"])
        table.add_row("Documents", str(stat["total_documents"]))
        table.add_row("Fragments", str(stat["total_fragments"]))
        table.add_row("Last Indexed", stat["last_indexed"] or "[dim]never[/dim]")
        console.print(table)


def present_repo_update(
    repo: RepositoryConfig,
    added_patterns: list[str],
    purged: int,
    no_purge: bool,
    console: Console,
) -> None:
    console.print(f"[green]✓[/green] Updated repository '[bold]{repo.name}[/bold]'")
    if added_patterns:
        console.print(f"  Added exclusion patterns: {', '.join(added_patterns)}")
    if purged:
        console.print(f"  Purged [bold]{purged}[/bold] previously-indexed document(s) matching new exclusions")
    elif added_patterns and not no_purge:
        console.print("  [dim]No previously-indexed documents matched the new exclusions[/dim]")


def present_repo_list(repos: list[RepositoryConfig], console: Console) -> None:
    if not repos:
        console.print("[dim]No repositories configured.[/dim]")
        return

    table = Table(title="Repositories", show_header=True, header_style="bold cyan", expand=True)
    table.add_column("Name", style="bold", no_wrap=True)
    table.add_column("Path")
    table.add_column("File Types")
    table.add_column("Embed", no_wrap=True)
    table.add_column("Image", no_wrap=True)
    table.add_column("Excludes")

    for repo in repos:
        embed_info = repo.embedding_provider
        if repo.embedding_model:
            embed_info += f"\n{repo.embedding_model}"

        image_info = repo.image_pipeline
        if repo.image_pipeline == "vlm" and repo.image_vlm_model:
            image_info += f"\n{repo.image_vlm_model}"

        table.add_row(
            repo.name,
            repo.path,
            ", ".join(repo.file_types),
            embed_info,
            image_info,
            ", ".join(repo.exclude_patterns) if repo.exclude_patterns else "[dim]none[/dim]",
        )

    console.print(table)


def _no_results(results: list, console: Console) -> bool:
    if not results:
        console.print("[dim]No results found.[/dim]")
        return True
    return False


def present_fragment_results(results: list[SearchResult], console: Console) -> None:
    if _no_results(results, console):
        return
    for result in results:
        console.print(
            Panel(
                result.text,
                title=f"[bold]{result.document_path}[/bold] (fragment {result.fragment_index})",
                subtitle=f"distance: {result.distance:.4f}",
                border_style="cyan",
            )
        )


def present_document_results(results: list[DocumentSearchResult], console: Console) -> None:
    if _no_results(results, console):
        return
    for doc_result in results:
        top_fragment = doc_result.top_fragments[0] if doc_result.top_fragments else None
        if top_fragment and len(top_fragment.text) > 200:
            preview = top_fragment.text[:200] + "..."
        else:
            preview = top_fragment.text if top_fragment else ""
        console.print(
            Panel(
                preview,
                title=f"[bold]{doc_result.document_path}[/bold]",
                subtitle=(f"best distance: {doc_result.best_distance:.4f} | {len(doc_result.top_fragments)} fragments"),
                border_style="green",
            )
        )


def present_pack_result(result: PackResult, console: Console) -> None:
    console.print(f"[green]✓[/green] Packed [bold]{result.total_files}[/bold] files into {result.archive_path}")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Category", no_wrap=True)
    table.add_column("Archive Path")
    for entry in result.entries:
        table.add_row(entry.category, entry.archive_path)
    console.print(table)
