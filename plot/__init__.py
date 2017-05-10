import matplotlib
from matplotlib import pyplot as plt

def get_formatted_plot(fnum=None, fsize=(4,3), textsize=8, scale=0.55):
    """Create a plot objected formatted in Times New Roman. Doesn't require arguments. 
    Returns axis object but this is not necessary to assign to memory if you call the plot function
    before calling this function again."""


    if fnum is not None:
        ax = plt.figure(num=fnum, figsize=fsize)
    else:
        ax = plt.figure(figsize=fsize)

    # Set matplotlib default font
    font = {'family': 'Times New Roman',
            'weight': 'normal',
            'size': textsize/scale}

    matplotlib.rc('font', **font)

    # Remove the plot frame lines. They are unnecessary chartjunk.
    ax = plt.subplot(111)
    ax.spines["top"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Ensure that the axis ticks only show up on the bottom and left of the plot.
    # Ticks on the right and top of the plot are generally unnecessary chartjunk.
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

    return ax

def format_plot_axis(x_placement_range, x_label_range, y_placement_range, y_label_range):
    """Format plot axis ticks and number ranges. Arguments are lists identifying value at which to place a tick
    and the string/value to place there.
    
    e.g. format_plot_axis( [locations to place labels on x-axis], [labels for x-axis],
                            [locations to place labels on y-axis], [labels for y-axis])"""

    # Make sure your axis ticks are large enough to be easily read.
    # You don't want your viewers squinting to read your plot.
    plt.xticks(x_placement_range, x_label_range)
    plt.yticks(y_placement_range, y_label_range)

    # Provide tick lines across the plot to help your viewers trace along
    # the axis ticks. Make sure that the lines are light and small so they
    # don't obscure the primary data lines.
    for y in y_placement_range:
        plt.plot(x_placement_range, [y] * len(x_placement_range), "--", lw=0.5, color="black", alpha=0.3)

    for x in x_placement_range:
        plt.plot([x] * len(y_placement_range), y_placement_range, ":", lw=0.5, color="black", alpha=0.3)

    # Remove the tick marks; they are unnecessary with the tick lines we just plotted.
    plt.tick_params(axis="both", which="both", bottom="off", top="off",
                    labelbottom="on", left="off", right="off", labelleft="on")