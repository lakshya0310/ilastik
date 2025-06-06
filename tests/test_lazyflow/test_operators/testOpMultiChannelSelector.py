import numpy
import pytest
import vigra

from lazyflow.operators import OpArrayPiper, OpMultiChannelSelector


@pytest.fixture
def random_data_5c():
    data = numpy.random.randint(0, 256, (10, 5, 5), dtype="uint8")
    return vigra.taggedView(data, "yxc")


def test_raises_channel_not_last(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxz")
    op = OpMultiChannelSelector(graph=graph)
    with pytest.raises(ValueError):
        op.Input.setValue(vdata)


def test_notready_if_selected_channel_not_in_data(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(vdata)
    op.SelectedChannels.setValue([1])

    assert not op.Output.ready()


def test_unready_if_selected_channel_not_in_data(graph):
    data = numpy.random.randint(0, 256, (10, 5, 2), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")

    op_piper = OpArrayPiper(graph=graph)

    op = OpMultiChannelSelector(graph=graph)
    op.Input.connect(op_piper.Output)
    op.SelectedChannels.setValue([1])
    op_piper.Input.setValue(vdata)

    assert op.Output.ready()

    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")
    op_piper.Input.setValue(vdata)

    assert not op.Output.ready()


def test_trivial_operation(graph):
    data = numpy.random.randint(0, 256, (10, 5, 1), dtype="uint8")
    vdata = vigra.taggedView(data, "yxc")

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(vdata)
    op.SelectedChannels.setValue([0])

    output = op.Output[()].wait()

    numpy.testing.assert_array_equal(output, data)


@pytest.mark.parametrize(
    "selected_channel",
    [
        0,
        1,
        2,
        3,
        4,
    ],
)
def test_get_single_channel(graph, selected_channel, random_data_5c):
    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(random_data_5c)
    op.SelectedChannels.setValue([selected_channel])

    output = op.Output[()].wait()

    numpy.testing.assert_array_equal(output, random_data_5c[..., (selected_channel,)])


def test_selected_channel_change(graph, random_data_5c):
    selected_channels = range(1, 5)

    is_dirty = False

    def set_dirty(*args, **kwargs):
        nonlocal is_dirty
        assert not is_dirty
        is_dirty = True

    op = OpMultiChannelSelector(graph=graph)
    op.Input.setValue(random_data_5c)
    # no change expected as its the default value
    op.SelectedChannels.setValue([0])

    assert not is_dirty

    for selected_channel in selected_channels:
        is_dirty = True
        op.SelectedChannels.setValue([selected_channel])
        assert is_dirty

        output = op.Output[()].wait()
        numpy.testing.assert_array_equal(output, random_data_5c[..., (selected_channel,)])


@pytest.mark.parametrize(
    "selected_channels",
    [
        (4,),
        (0, 1, 2, 3, 4),
        (4, 3, 2, 1, 0),
        (1, 2),
        (2, 4),
        (4, 2),
        (3, 2, 4),
        (1, 1, 1),
    ],
)
def test_select_multi_channels(graph, selected_channels, random_data_5c):
    op = OpMultiChannelSelector(graph=graph)
    op.SelectedChannels.setValue(selected_channels)
    op.Input.setValue(random_data_5c)

    output = op.Output[()].wait()
    numpy.testing.assert_array_equal(output, random_data_5c[..., selected_channels])
