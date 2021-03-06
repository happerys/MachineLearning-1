# Copyright 2017 Zangbo. All Rights Reserved.
# A simple MNIST classifier which displays summaries in TensorBoard.
# This is an unimpressive MNIST model, but it is a good example of using
# tf.name_scope to make a graph legible in the TensorBoard graph explorer, and of
# naming summary tags so that they are grouped meaningfully in TensorBoard.
# ==============================================================================
import os
import tensorflow as tf

### MNIST datasets ###
LOGDIR = '/tmp/mnist_tutorial/'
from tensorflow.examples.tutorials.mnist import input_data
mnist = input_data.read_data_sets(train_dir=LOGDIR + 'data', one_hot=True)

def conv_layer(input, size_in, size_out, name="conv"):
  with tf.name_scope(name):
    w = tf.Variable(tf.truncated_normal([5, 5, size_in, size_out], stddev=0.1), name="W")
    b = tf.Variable(tf.constant(0.1, shape=[size_out]), name="B")
    conv = tf.nn.conv2d(input, w, strides=[1, 1, 1, 1], padding="SAME")
    act = tf.nn.relu(conv + b)
    tf.summary.histogram("weights", w)
    tf.summary.histogram("biases", b)
    tf.summary.histogram("activations", act)
    return tf.nn.max_pool(act, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding="SAME")


def fc_layer(input, size_in, size_out, name="fc"):
  with tf.name_scope(name):
    w = tf.Variable(tf.truncated_normal([size_in, size_out], stddev=0.1), name="W")
    b = tf.Variable(tf.constant(0.1, shape=[size_out]), name="B")
    act = tf.nn.relu(tf.matmul(input, w) + b)
    tf.summary.histogram("weights", w)
    tf.summary.histogram("biases", b)
    tf.summary.histogram("activations", act)
    return act


def mnist_model(learning_rate, use_two_conv, use_two_fc, use_dropout, hparam):
  tf.reset_default_graph()
  sess = tf.Session()

  # Setup placeholders, and reshape the data
  x = tf.placeholder(tf.float32, shape=[None, 784], name="x")
  x_image = tf.reshape(x, [-1, 28, 28, 1])
  tf.summary.image('input', x_image, 3)
  y = tf.placeholder(tf.float32, shape=[None, 10], name="labels")

  if use_two_conv:
    conv1 = conv_layer(x_image, 1, 32, "conv1")
    conv_out = conv_layer(conv1, 32, 64, "conv2")
  else:
    conv1 = conv_layer(x_image, 1, 64, "conv")
    conv_out = tf.nn.max_pool(conv1, ksize=[1, 2, 2, 1], strides=[1, 2, 2, 1], padding="SAME")

  flattened = tf.reshape(conv_out, [-1, 7 * 7 * 64])


  if use_two_fc:
    fc1 = fc_layer(flattened, 7 * 7 * 64, 1024, "fc1")
    if use_dropout:
      with tf.name_scope('dropout'):
        keep_prob = tf.constant(0.5, name='keep_prob')
        fc1_dropout = tf.nn.dropout(fc1, keep_prob)
        logits = fc_layer(fc1_dropout, 1024, 10, "fc2")
    else:
      logits = fc_layer(fc1, 1024, 10, "fc2")
  else:
    logits = fc_layer(flattened, 7*7*64, 10, "fc")

  with tf.name_scope("xent"):
    xent = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits(
            logits=logits, labels=y), name="xent")
    tf.summary.scalar("xent", xent)

  with tf.name_scope("train"):
    train_step = tf.train.AdamOptimizer(learning_rate).minimize(xent)

  with tf.name_scope("accuracy"):
    correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(y, 1))
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
    tf.summary.scalar("accuracy", accuracy)

  summ = tf.summary.merge_all()

  sess.run(tf.global_variables_initializer())
  writer = tf.summary.FileWriter(LOGDIR + hparam)
  writer.add_graph(sess.graph)

  for i in range(2001):
    batch = mnist.train.next_batch(100)
    if i % 5 == 0:
      [train_accuracy, s] = sess.run([accuracy, summ], feed_dict={x: batch[0], y: batch[1]})
      writer.add_summary(s, i)
    if i % 100 == 99:  # Record execution statistics
      run_options = tf.RunOptions(trace_level=tf.RunOptions.FULL_TRACE)
      run_metadata = tf.RunMetadata()
      _, s = sess.run([train_step, summ],
                      feed_dict={x: batch[0], y: batch[1]},
                      options=run_options,
                      run_metadata=run_metadata)
      writer.add_run_metadata(run_metadata, 'step%03d' % i) #add_run_metadata(run_metadata, tag, global_step=None)
      writer.add_summary(s, i)
    else:
      sess.run(train_step, feed_dict={x: batch[0], y: batch[1]})
  writer.close()
  sess.close()

def make_hparam_string(learning_rate, use_two_fc, use_two_conv, use_dropout):
  conv_param = "conv=2" if use_two_conv else "conv=1"
  fc_param = "fc=2" if use_two_fc else "fc=1"
  dropout_param = "dropout" if use_dropout else "no_dropout"
  return "lr_%.0E,%s,%s,%s" % (learning_rate, conv_param, fc_param,dropout_param)

def main():
  if tf.gfile.Exists(LOGDIR):
    tf.gfile.DeleteRecursively(LOGDIR)
  tf.gfile.MakeDirs(LOGDIR)
  #Add other param to try different learning rate
  for learning_rate in [1E-4]:
    # Try different model architectures
    for use_two_fc in [True, False]:
      for use_two_conv in [True, False]:
        for use_dropout in [True, False]:
          # Construct a hyperparameter string for each one (example: "lr_1E-4,fc=2,conv=2,dropout)
          hparam = make_hparam_string(learning_rate, use_two_fc, use_two_conv, use_dropout)
          print('Starting run for %s' % hparam)

          # Actually run with the new settings
          mnist_model(learning_rate, use_two_fc, use_two_conv, use_dropout, hparam)


if __name__ == '__main__':
  main()