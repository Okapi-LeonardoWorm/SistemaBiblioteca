def checkpoint_progress(processed: int, total: int, last_progress: int) -> int:
    if total <= 0:
        return 100

    raw_percent = int((processed / total) * 100)
    current_checkpoint = min(100, (raw_percent // 10) * 10)
    if current_checkpoint > last_progress:
        return current_checkpoint
    return last_progress
