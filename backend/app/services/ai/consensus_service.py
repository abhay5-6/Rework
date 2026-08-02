def calculate_consensus_score(
    memory
):
    

    total = (

        memory.agreement_count

        +

        memory.disagreement_count
    )

    if total == 0:
        return 1.0

    agreement_ratio = (
        memory.agreement_count
        / total
    )

    return max(
        0.3,
        agreement_ratio
    )