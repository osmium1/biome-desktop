using System;
using System.Windows;
using System.Windows.Media.Animation;

namespace Biome.Desktop.App.Windowing
{
    public partial class SpeedboostOverlay : Window
    {
        public SpeedboostOverlay()
        {
            InitializeComponent();
        }

        public void StartAnimation(bool isDemo)
        {
            // Position the overlay in the bottom-right corner, hovering above the taskbar.
            var workArea = SystemParameters.WorkArea;
            this.Left = workArea.Right - this.Width;
            this.Top = workArea.Bottom - this.Height;

            this.Show();

            // Kick off the storyboard; loop forever during live sends, single playback for demos.
            if (this.Resources["BoostAnimation"] is Storyboard sb)
            {
                sb.RepeatBehavior = isDemo ? new RepeatBehavior(1) : RepeatBehavior.Forever;
                sb.Begin();
            }
        }

        public void StopAnimation()
        {
            if (this.Resources["BoostAnimation"] is Storyboard sb)
            {
                sb.Stop();
            }
            this.Close();
        }

        private void Storyboard_Completed(object sender, EventArgs e)
        {
            // Defensive close in case a single-shot animation finishes naturally.
            this.Close();
        }
    }
}