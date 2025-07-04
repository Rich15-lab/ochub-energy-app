import io
import matplotlib.pyplot as plt
import pandas as pd


def generate_gauge_chart(df):
    """
    Generates a 3-panel gauge chart showing voltage, intensity, and energy.
    """
    fig, axs = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axs[0].plot(df.index, df['Voltage'], color='green')
    axs[0].axhline(3.0, color='red', linestyle='--')
    axs[0].set_ylabel("Voltage (V)")

    axs[1].plot(df.index, df['Intensity'], color='blue')
    axs[1].axhline(8, color='red', linestyle='--')
    axs[1].set_ylabel("Intensity (A)")

    axs[2].plot(df.index, df['Energy'], color='orange')
    axs[2].axhline(10, color='red', linestyle='--')
    axs[2].set_ylabel("Energy (J)")

    for ax in axs:
        ax.grid(True)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)

    return buf


def generate_chart_image_file(voltage_data, intensity_data, energy_data, time_labels):
    """
    Generates a smoothed line chart image file from session data for use in PDF reports.
    """
    df = pd.DataFrame({
        "Voltage": voltage_data,
        "Intensity": intensity_data,
        "Energy": energy_data
    }, index=time_labels)

    df = df.dropna().iloc[::5].rolling(window=10).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    df.plot(ax=ax)
    ax.set_title("Smoothed Voltage, Intensity & Energy Over Time")
    ax.set_ylabel("Sensor Value")
    ax.set_xlabel("Time")
    ax.grid(True)
    plt.xticks(rotation=30)

    chart_path = "ochub_chart_for_pdf.png"
    plt.savefig(chart_path)
    plt.close(fig)

    return chart_path


def generate_gauge_chart_image(voltage, intensity, energy):
    """
    Generates a horizontal gauge summary chart for voltage, intensity, and energy.
    """
    fig, axs = plt.subplots(3, 1, figsize=(5, 2.5))

    colors = ['green' if val < limit else 'red' for val, limit in zip([voltage, intensity, energy], [3.0, 8, 10])]
    titles = ['Voltage (V)', 'Intensity (A)', 'Energy (J)']
    values = [voltage, intensity, energy]
    limits = [4.2, 20, 50]

    for ax, val, title, color, limit in zip(axs, values, titles, colors, limits):
        ax.barh(0, val, color=color)
        ax.set_xlim(0, limit)
        ax.set_title(f"{title}: {val:.2f}", fontsize=10)
        ax.axis('off')

    plt.tight_layout()
    path = "ochub_gauges_for_pdf.png"
    plt.savefig(path)
    plt.close(fig)

    return path
