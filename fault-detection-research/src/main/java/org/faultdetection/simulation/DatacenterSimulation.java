package org.faultdetection.simulation;

import org.cloudsimplus.allocationpolicies.VmAllocationPolicySimple;
import org.cloudsimplus.brokers.DatacenterBroker;
import org.cloudsimplus.brokers.DatacenterBrokerSimple;
import org.cloudsimplus.cloudlets.Cloudlet;
import org.cloudsimplus.cloudlets.CloudletSimple;
import org.cloudsimplus.core.CloudSimPlus;
import org.cloudsimplus.datacenters.Datacenter;
import org.cloudsimplus.datacenters.DatacenterSimple;
import org.cloudsimplus.hosts.Host;
import org.cloudsimplus.hosts.HostSimple;
import org.cloudsimplus.power.models.PowerModelHostSimple;
import org.cloudsimplus.resources.Pe;
import org.cloudsimplus.resources.PeSimple;
import org.cloudsimplus.schedulers.cloudlet.CloudletSchedulerTimeShared;
import org.cloudsimplus.utilizationmodels.UtilizationModelDynamic;
import org.cloudsimplus.utilizationmodels.UtilizationModelFull;
import org.cloudsimplus.vms.Vm;
import org.cloudsimplus.vms.VmSimple;
import org.faultdetection.config.ResearchConfig;
import org.faultdetection.simulation.faults.FaultInjector;
import org.faultdetection.telemetry.TelemetryWriter;
import org.faultdetection.telemetry.collectors.MultiModalTelemetryCollector;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;

/**
 * CloudSim-based datacenter simulation for generating telemetry data
 * with controlled fault injection.
 */
public class DatacenterSimulation {
    private static final Logger logger = LoggerFactory.getLogger(DatacenterSimulation.class);

    private final ResearchConfig config;
    private CloudSimPlus simulation;
    private Datacenter datacenter;
    private List<Vm> vmList;
    private MultiModalTelemetryCollector telemetryCollector;
    private TelemetryWriter telemetryWriter;
    private FaultInjector faultInjector;

    public DatacenterSimulation(ResearchConfig config) {
        this.config = config;
    }

    /**
     * Run the complete simulation and return the path to generated telemetry data.
     */
    public Path run() throws Exception {
        logger.info("Starting datacenter simulation...");
        logger.info("Hosts: {}, VMs: {}, Cloudlets: {}, Duration: {}s",
            config.getNumberOfHosts(),
            config.getNumberOfVms(),
            config.getNumberOfCloudlets(),
            config.getSimulationDuration());

        // Initialize simulation
        simulation = new CloudSimPlus();

        // Create datacenter
        datacenter = createDatacenter();

        // Create broker
        DatacenterBroker broker = new DatacenterBrokerSimple(simulation);

        // Create VMs and Cloudlets
        vmList = createVms();
        List<Cloudlet> cloudletList = createCloudlets();

        broker.submitVmList(vmList);
        broker.submitCloudletList(cloudletList);

        // Setup telemetry collection
        setupTelemetryCollection();

        // Setup fault injection
        setupFaultInjection();

        // Run simulation
        simulation.terminateAt(config.getSimulationDuration());
        simulation.start();

        // Cleanup
        telemetryWriter.close();
        logger.info("Simulation completed successfully");

        return telemetryWriter.getOutputPath();
    }

    private Datacenter createDatacenter() {
        List<Host> hostList = new ArrayList<>();

        for (int i = 0; i < config.getNumberOfHosts(); i++) {
            Host host = createHost(i);
            hostList.add(host);
        }

        logger.info("Created {} hosts", hostList.size());
        return new DatacenterSimple(simulation, hostList, new VmAllocationPolicySimple());
    }

    private Host createHost(int id) {
        long mipsPerPe = 1000; // MIPS per core
        int numberOfPes = 8; // cores per host
        long ram = 32_000; // MB
        long storage = 1_000_000; // MB
        long bandwidth = 10_000; // Mbps

        List<Pe> peList = new ArrayList<>();
        for (int i = 0; i < numberOfPes; i++) {
            peList.add(new PeSimple(mipsPerPe));
        }

        HostSimple host = new HostSimple(ram, bandwidth, storage, peList);
        host.setId(id);

        // Power model: 200W static + up to 300W dynamic based on CPU usage
        PowerModelHostSimple powerModel = new PowerModelHostSimple(300, 200);
        host.setPowerModel(powerModel);

        return host;
    }

    private List<Vm> createVms() {
        List<Vm> vms = new ArrayList<>();

        for (int i = 0; i < config.getNumberOfVms(); i++) {
            Vm vm = createVm(i);
            vms.add(vm);
        }

        logger.info("Created {} VMs", vms.size());
        return vms;
    }

    private Vm createVm(int id) {
        long mips = 1000;
        int pesNumber = 2;
        long ram = 2048; // MB
        long bandwidth = 1000; // Mbps
        long storage = 10_000; // MB

        Vm vm = new VmSimple(id, mips, pesNumber);
        vm.setRam(ram)
          .setBw(bandwidth)
          .setSize(storage)
          .setCloudletScheduler(new CloudletSchedulerTimeShared());

        return vm;
    }

    private List<Cloudlet> createCloudlets() {
        List<Cloudlet> cloudlets = new ArrayList<>();

        long length = 10_000; // MI (Million Instructions)
        int pesNumber = 1;

        for (int i = 0; i < config.getNumberOfCloudlets(); i++) {
            Cloudlet cloudlet = new CloudletSimple(length, pesNumber);
            cloudlet.setUtilizationModelCpu(new UtilizationModelDynamic(0.5));
            cloudlet.setUtilizationModelRam(new UtilizationModelDynamic(0.3));
            cloudlet.setUtilizationModelBw(new UtilizationModelFull());
            cloudlets.add(cloudlet);
        }

        logger.info("Created {} cloudlets", cloudlets.size());
        return cloudlets;
    }

    private void setupTelemetryCollection() throws Exception {
        // Initialize telemetry collector
        telemetryCollector = new MultiModalTelemetryCollector();
        telemetryCollector.initialize();

        // Initialize telemetry writer
        Path telemetryPath = Paths.get(config.getTelemetryOutputPath(), "telemetry.csv");
        telemetryWriter = new TelemetryWriter(telemetryPath);

        // Register clock tick listener for periodic telemetry collection
        simulation.addOnClockTickListener(info -> {
            try {
                double currentTime = info.getTime();

                // Collect telemetry at configured intervals
                if (currentTime % config.getTelemetryInterval() < 0.1) {
                    var snapshot = telemetryCollector.collect(
                        currentTime,
                        datacenter.getHostList(),
                        vmList
                    );
                    telemetryWriter.write(snapshot);
                }
            } catch (Exception e) {
                logger.error("Error collecting telemetry at time {}", info.getTime(), e);
            }
        });

        logger.info("Telemetry collection configured (interval: {}s)", config.getTelemetryInterval());
    }

    private void setupFaultInjection() {
        faultInjector = new FaultInjector(config, datacenter.getHostList());
        faultInjector.initialize();

        // Register listener for fault injection
        simulation.addOnClockTickListener(info -> {
            double currentTime = info.getTime();
            if (currentTime >= config.getFaultInjectionStart()) {
                faultInjector.injectFaults(currentTime);
            }
        });

        logger.info("Fault injection configured (start time: {}s, probability: {})",
            config.getFaultInjectionStart(),
            config.getFaultProbability());
    }

    public CloudSimPlus getSimulation() {
        return simulation;
    }

    public Datacenter getDatacenter() {
        return datacenter;
    }

    public List<Vm> getVmList() {
        return vmList;
    }
}
