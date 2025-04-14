import sys
import io
import mpld3
import traceback


def exec_code_as_string(code, namespace, create_plot_js):
    res = {}
    old_stdout = sys.stdout
    code_out = buffer = io.StringIO()
    code_error = ""

    # capture output
    sys.stdout = code_out

    try:
        exec(code, namespace)
    except Exception as e:
        code_error = traceback.format_exc()

    if create_plot_js and 'plt' in namespace:
        plt = namespace['plt']
        fig = plt.gcf()
        plot_height = max(5, len(fig.get_axes()) * 1.5)
        fig.set_size_inches(6, plot_height)
        fig.tight_layout(pad=0.1)
        plot = mpld3.fig_to_dict(fig)
        plt.close('all')
        res['plot'] = plot

    # restore stdout and stderr
    sys.stdout = old_stdout

    res['error'] = code_error

    sys_out = code_out.getvalue()
    print("output:\n%s" % sys_out)
    res['console'] = sys_out
    code_out.close()

    return res
