#include <ros/ros.h>

#include <sensor_msgs/PointCloud2.h>
#include <pcl_ros/point_cloud.h>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

// Filters
#include <pcl/filters/passthrough.h>
#include <pcl/filters/statistical_outlier_removal.h>
#include <pcl/filters/voxel_grid.h>
#include <pcl/filters/extract_indices.h>

// Sample Concensus
#include <pcl/sample_consensus/method_types.h>
#include <pcl/sample_consensus/model_types.h>

// Segmentation
#include <pcl/segmentation/sac_segmentation.h>
#include <pcl/segmentation/extract_clusters.h>

#include <pcl/common/common.h> // minMax3d
#include <pcl/kdtree/kdtree.h> // KdTree

ros::Publisher publisher;
ros::Subscriber subscriber;

typedef pcl::PointCloud<pcl::PointXYZRGB> PointCloud;
typedef pcl::PointXYZRGB Point;

void cloudCallback(const pcl::PointCloud<pcl::PointXYZRGB>::ConstPtr& inputCloud) {

    //std::cout << "Before: " << inputCloud->size() << std::endl;

    // Filter cloud based on z-value
    PointCloud::Ptr cloudPassthrough(new PointCloud);
    pcl::PassThrough<Point> passthrough;
    passthrough.setInputCloud(inputCloud);
    passthrough.setFilterFieldName("z");
    passthrough.setFilterLimits(0.0, 1.0); // 0-1m
    passthrough.filter(*cloudPassthrough);

    PointCloud::Ptr cloudDownsampled(new PointCloud);
    pcl::VoxelGrid<Point> downsample;
    downsample.setInputCloud(cloudPassthrough);
    downsample.setLeafSize(0.01f, 0.01f, 0.01f);
    downsample.filter(*cloudDownsampled);

    PointCloud::Ptr cloudFiltered(new PointCloud);
    pcl::SACSegmentation<Point> segmentation;
    pcl::PointIndices::Ptr inliers(new pcl::PointIndices);
    pcl::ModelCoefficients::Ptr coefficients(new pcl::ModelCoefficients);
    pcl::PointCloud<Point>::Ptr cloudPlane(new pcl::PointCloud<Point>);
    segmentation.setOptimizeCoefficients(true);
    segmentation.setModelType(pcl::SACMODEL_PLANE);
    segmentation.setMethodType(pcl::SAC_RANSAC);
    segmentation.setMaxIterations(100);
    segmentation.setDistanceThreshold(0.02);

    int numPoints = (int) cloudDownsampled->points.size();

    while (cloudDownsampled->points.size() > 0.1 * numPoints) {

        segmentation.setInputCloud(cloudDownsampled);
        segmentation.segment(*inliers, *coefficients);

        if (inliers->indices.size() == 0) {
            std::cout << "No planar model" << std::endl;
            break;
        }

        // Extract the planar inliers from the input cloud
        pcl::ExtractIndices<Point> extract;
        extract.setInputCloud(cloudDownsampled);
        extract.setIndices(inliers);
        extract.setNegative(false);
        extract.filter(*cloudPlane);
        extract.setNegative(true);
        extract.filter(*cloudFiltered);
        *cloudDownsampled = *cloudFiltered;
    }

    // Creating the KdTree object for the search method of the extraction
    pcl::search::KdTree<Point>::Ptr tree (new pcl::search::KdTree<Point>);
    tree->setInputCloud(cloudDownsampled);

    std::vector<pcl::PointIndices> clusterIndices;
    pcl::EuclideanClusterExtraction<Point> extract;
    extract.setClusterTolerance(0.04); // 2cm
    extract.setMinClusterSize(100);
    extract.setMaxClusterSize(2000);
    extract.setSearchMethod(tree);
    extract.setInputCloud(cloudDownsampled);
    extract.extract(clusterIndices);

    std::cout << "Clusters found: " << clusterIndices.size() << std::endl;

    for (std::vector<pcl::PointIndices>::const_iterator it = clusterIndices.begin(); it != clusterIndices.end(); ++it) {

    }

    publisher.publish(cloudDownsampled);



    /*//std::cout << "After: " << cloudPassthrough->size() << std::endl;
    Point min;
    Point max;
    pcl::getMinMax3D(*cloudPassthrough, min, max);

    std::cout << "Min: " << min << std::endl;
    std::cout << "Max: " << max << std::endl;*/

    /**/

    /*boost::shared_ptr<pcl::visualization::PCLVisualizer> viewer (new pcl::visualization::PCLVisualizer ("3D Viewer"));
    viewer->setBackgroundColor (0, 0, 0);
    pcl::visualization::PointCloudColorHandlerRGBField<pcl::PointXYZRGB> rgb(inputCloud);
    viewer->addPointCloud<pcl::PointXYZRGB> (inputCloud, rgb, "sample cloud");*/

    /*// Remove statistical outliers
    PointCloud::Ptr cloudDenoised(new PointCloud);
    pcl::StatisticalOutlierRemoval<Point> sor;
    sor.setInputCloud(cloudFiltered);
    sor.setMeanK(50);
    sor.setStddevMulThresh(1.0);
    sor.filter(*cloudDenoised);*/



}

int main(int argc, char** argv) {

    ros::init(argc, argv, "detector");
    ros::NodeHandle nh;

    subscriber = nh.subscribe<pcl::PointCloud<pcl::PointXYZRGB> >("/camera/depth_registered/points", 1, cloudCallback);
    publisher = nh.advertise<pcl::PointCloud<pcl::PointXYZRGB> >("/pointcloud", 1);

    ros::spin();
}
