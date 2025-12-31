import matplotlib.pyplot as plt
import numpy as np


def generate_radar_chart(scores, output_path):
    labels = list(scores.keys())
    values = list(scores.values())

    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    values = values + values[:1]
    angles = np.concatenate([angles, [angles[0]]])

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.25)

    ax.set_thetagrids(angles[:-1] * 180 / np.pi, labels)
    ax.set_ylim(0, 5)
    ax.set_yticklabels([])

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()
